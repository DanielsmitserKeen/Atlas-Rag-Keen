"""
Extract KPI Data from Dashboard HTML and prepare for Supabase upload
This script extracts company performance metrics and creates documents for the RAG system
"""

import json
import re
from datetime import datetime

def extract_company_data_from_html(html_file_path):
    """Extract COMPANY_DATA from the HTML file"""
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Find the COMPANY_DATA JavaScript object
    pattern = r'const COMPANY_DATA\s*=\s*({[\s\S]*?});'
    match = re.search(pattern, html_content)
    
    if not match:
        raise ValueError("Could not find COMPANY_DATA in HTML file")
    
    # Extract the JavaScript object as string
    js_object = match.group(1)
    
    # Convert JavaScript object to Python dict
    # Replace single quotes with double quotes for JSON compatibility
    # Handle property names without quotes
    js_object = re.sub(r"'([^']+)':", r'"\1":', js_object)  # 'key': -> "key":
    js_object = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', js_object)  # key: -> "key":
    js_object = re.sub(r":\s*'([^']*)'", r': "\1"', js_object)  # : 'value' -> : "value"
    
    # Parse as JSON
    try:
        company_data = json.loads(js_object)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        print("Extracted object:", js_object[:500])
        raise
    
    return company_data

def create_kpi_documents(company_data):
    """Convert KPI data into document chunks for RAG system"""
    documents = []
    
    metrics_info = {
        'growth': {
            'full_name': 'Revenue Growth',
            'description': 'Year-over-year revenue growth percentage',
            'unit': '%'
        },
        'rule40': {
            'full_name': 'Rule of 40',
            'description': 'Growth rate + profit margin (Rule of 40 benchmark)',
            'unit': '%'
        },
        'gross-margin': {
            'full_name': 'Gross Margin',
            'description': 'Gross profit margin percentage',
            'unit': '%'
        }
    }
    
    # Create overview documents for each metric
    for metric_key, years_data in company_data.items():
        metric_info = metrics_info.get(metric_key, {})
        metric_name = metric_info.get('full_name', metric_key)
        
        for year, companies in years_data.items():
            # Create a summary document for this metric/year
            company_list = []
            for company_name, data in companies.items():
                company_list.append(f"{company_name}: {data['value']}{metric_info.get('unit', '')} (ARR Bucket: {data['bucket']})")
            
            summary_content = f"""
{metric_name} - Year {year}
{'=' * 50}

Metric: {metric_name}
Description: {metric_info.get('description', 'Performance metric')}
Year: {year}
Number of Portfolio Companies Reported: {len(companies)}

Company Performance:
{chr(10).join('- ' + item for item in company_list)}

ARR Buckets Represented:
{', '.join(sorted(set(data['bucket'] for data in companies.values())))}
"""
            
            documents.append({
                'filename': f'KPI_Dashboard_{metric_key}_{year}.txt',
                'content': summary_content.strip(),
                'metadata': {
                    'source_type': 'kpi_dashboard',
                    'metric': metric_key,
                    'year': year,
                    'company_count': len(companies),
                    'date_added': datetime.now().isoformat()
                }
            })
            
            # Create individual company documents
            for company_name, data in companies.items():
                company_content = f"""
Company Performance Report: {company_name}

Metric: {metric_name}
Year: {year}
Value: {data['value']}{metric_info.get('unit', '')}
ARR Bucket: {data['bucket']}

Description: 
{company_name} reported a {metric_name.lower()} of {data['value']}{metric_info.get('unit', '')} in {year}. 
The company is in the {data['bucket']} ARR (Annual Recurring Revenue) bucket.

{metric_info.get('description', 'Performance metric tracked by Keen Venture Partners.')}

This data is from the Keen Venture Partners KPI Dashboard and represents portfolio company performance metrics.
"""
                
                documents.append({
                    'filename': f'Company_{company_name}_{metric_key}_{year}.txt',
                    'content': company_content.strip(),
                    'metadata': {
                        'source_type': 'kpi_dashboard',
                        'company': company_name,
                        'metric': metric_key,
                        'year': year,
                        'value': data['value'],
                        'arr_bucket': data['bucket'],
                        'date_added': datetime.now().isoformat()
                    }
                })
    
    # Create cross-company comparison documents
    for metric_key, years_data in company_data.items():
        for year, companies in years_data.items():
            metric_info = metrics_info.get(metric_key, {})
            metric_name = metric_info.get('full_name', metric_key)
            
            # Sort companies by value
            sorted_companies = sorted(companies.items(), key=lambda x: x[1]['value'], reverse=True)
            
            # Top performers
            top_5 = sorted_companies[:min(5, len(sorted_companies))]
            top_content = f"""
Top Performers - {metric_name} {year}
{'=' * 50}

The highest performing companies by {metric_name.lower()} in {year}:

"""
            for i, (company, data) in enumerate(top_5, 1):
                top_content += f"{i}. {company}: {data['value']}{metric_info.get('unit', '')} (ARR: {data['bucket']})\n"
            
            top_content += f"""

Analysis:
These companies represent the top performers in {metric_name.lower()} among Keen Venture Partners' portfolio companies for {year}.
The performance spans across different ARR buckets: {', '.join(set(data['bucket'] for _, data in top_5))}.
"""
            
            documents.append({
                'filename': f'Top_Performers_{metric_key}_{year}.txt',
                'content': top_content.strip(),
                'metadata': {
                    'source_type': 'kpi_dashboard',
                    'metric': metric_key,
                    'year': year,
                    'report_type': 'top_performers',
                    'date_added': datetime.now().isoformat()
                }
            })
    
    # Create benchmark documents by ARR bucket
    for metric_key, years_data in company_data.items():
        for year, companies in years_data.items():
            metric_info = metrics_info.get(metric_key, {})
            metric_name = metric_info.get('full_name', metric_key)
            
            # Group by ARR bucket
            buckets = {}
            for company_name, data in companies.items():
                bucket = data['bucket']
                if bucket not in buckets:
                    buckets[bucket] = []
                buckets[bucket].append((company_name, data['value']))
            
            # Create bucket analysis document
            bucket_content = f"""
{metric_name} by ARR Bucket - {year}
{'=' * 50}

This analysis shows {metric_name.lower()} segmented by company size (ARR bucket) for {year}.

"""
            for bucket, companies_in_bucket in sorted(buckets.items()):
                values = [val for _, val in companies_in_bucket]
                avg_value = sum(values) / len(values)
                
                bucket_content += f"""
ARR Bucket: {bucket}
Companies: {len(companies_in_bucket)}
Average {metric_name}: {avg_value:.2f}{metric_info.get('unit', '')}
Companies in bucket: {', '.join(name for name, _ in companies_in_bucket)}

"""
            
            bucket_content += f"""
Key Insights:
- Portfolio companies are tracked across {len(buckets)} different ARR size segments
- This allows for size-appropriate benchmarking and performance comparison
- Data sourced from Keen Venture Partners KPI Dashboard {year}
"""
            
            documents.append({
                'filename': f'ARR_Bucket_Analysis_{metric_key}_{year}.txt',
                'content': bucket_content.strip(),
                'metadata': {
                    'source_type': 'kpi_dashboard',
                    'metric': metric_key,
                    'year': year,
                    'report_type': 'arr_bucket_analysis',
                    'date_added': datetime.now().isoformat()
                }
            })
    
    return documents

def save_documents_to_json(documents, output_file='kpi_documents.json'):
    """Save extracted documents to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(documents)} documents to {output_file}")
    
    # Print statistics
    metrics = set()
    years = set()
    companies = set()
    
    for doc in documents:
        if 'metric' in doc['metadata']:
            metrics.add(doc['metadata']['metric'])
        if 'year' in doc['metadata']:
            years.add(doc['metadata']['year'])
        if 'company' in doc['metadata']:
            companies.add(doc['metadata']['company'])
    
    print(f"\nStatistics:")
    print(f"- Total documents: {len(documents)}")
    print(f"- Metrics covered: {', '.join(sorted(metrics))}")
    print(f"- Years: {', '.join(sorted(years))}")
    print(f"- Unique companies: {len(companies)}")
    print(f"- Company names: {', '.join(sorted(companies))}")

if __name__ == '__main__':
    print("Extracting KPI data from dashboard...")
    
    html_file = 'KeenKPIDashboard.html'
    
    try:
        # Extract data
        company_data = extract_company_data_from_html(html_file)
        print(f"✓ Extracted data for {len(company_data)} metrics")
        
        # Create documents
        documents = create_kpi_documents(company_data)
        print(f"✓ Created {len(documents)} document chunks")
        
        # Save to JSON
        save_documents_to_json(documents)
        
        print("\n✓ KPI data extraction complete!")
        print("\nNext step: Run 'python upload_kpi_to_supabase.py' to upload to database")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
