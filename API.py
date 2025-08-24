import requests
import time
import csv
import sys
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


# --- 配置参数 ---
PAPER_ID = os.getenv("PAPER_ID")
OUTPUT_FILE = "citations_details_final.csv"

# API 的基础 URL
BASE_URL = "https://api.semanticscholar.org/graph/v1"

# 修正：移除了不支持的 'tldr' 字段
FIELDS = (
    "paperId,title,authors,year,venue,publicationVenue,externalIds,abstract,"
    "citationCount,influentialCitationCount,referenceCount,isOpenAccess"
)

# 修正：移除了对应的CSV表头
CSV_HEADER = [
    "citing_paper_id", "title", "authors", "year", "venue", "publication_venue", "doi", "abstract",
    "citation_count", "influential_citation_count", "reference_count", "is_open_access"
]


def get_citations():
    """
    获取指定文献的所有引文信息（包含详细元数据）并保存到 CSV 文件。
    """
    offset = 0
    limit = 100
    total_citations = 0
    
    print(f"准备下载文献 '{PAPER_ID}' 的引文（包含详细元数据）...")
    print(f"数据将保存到文件: {OUTPUT_FILE}")

    # 使用 'utf-8-sig' 编码以确保 Excel 兼容性
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(CSV_HEADER)

        while True:
            try:
                params = {
                    'fields': FIELDS,
                    'offset': offset,
                    'limit': limit
                }

                url = f"{BASE_URL}/paper/{PAPER_ID}/citations"
                print(f"正在请求第 {offset // limit + 1} 页数据 (offset={offset})...")
                response = requests.get(url, params=params, timeout=30)
                
                response.raise_for_status()

                data = response.json()
                citations = data.get('data', [])

                if not citations:
                    print("已获取所有引文数据。")
                    break

                for item in citations:
                    paper_info = item.get('citingPaper', {})
                    if not paper_info:
                        continue
                    
                    # --- 提取信息 ---
                    authors_list = paper_info.get('authors', [])
                    authors = "; ".join([author.get('name', 'N/A') for author in authors_list if author]) if authors_list else 'N/A'
                    doi = paper_info.get('externalIds', {}).get('DOI', 'N/A') if paper_info.get('externalIds') else 'N/A'
                    pub_venue_obj = paper_info.get('publicationVenue')
                    publication_venue_name = pub_venue_obj.get('name', 'N/A') if pub_venue_obj else 'N/A'
                    abstract = paper_info.get('abstract', 'N/A')
                    citation_count = paper_info.get('citationCount', 0)
                    influential_citation_count = paper_info.get('influentialCitationCount', 0)
                    reference_count = paper_info.get('referenceCount', 0)
                    is_open_access = paper_info.get('isOpenAccess', False)
                    # 移除：不再提取 tldr_summary

                    # --- 准备写入CSV的一行完整数据 ---
                    row = [
                        paper_info.get('paperId', 'N/A'),
                        paper_info.get('title', 'N/A'),
                        authors,
                        paper_info.get('year', 'N/A'),
                        paper_info.get('venue', 'N/A'),
                        publication_venue_name,
                        doi,
                        abstract,
                        citation_count,
                        influential_citation_count,
                        reference_count,
                        is_open_access
                        # 移除：不再将 tldr 添加到行中
                    ]
                    writer.writerow(row)

                total_citations += len(citations)
                sys.stdout.write(f"\r已成功下载 {total_citations} 篇引文。")
                sys.stdout.flush()

                if 'next' in data and data['next'] is not None:
                    offset = data['next']
                else:
                    print("\n已到达最后一页。")
                    break
                
                time.sleep(0.5)

            except requests.exceptions.HTTPError as e:
                print(f"\n请求失败，HTTP 错误: {e}")
                print(f"响应内容: {e.response.text}")
                break
            except requests.exceptions.RequestException as e:
                print(f"\n网络请求失败: {e}")
                print("等待10秒后重试...")
                time.sleep(10)
            except Exception as e:
                print(f"\n发生未知错误: {e}")
                break
    
    if total_citations > 0:
        print(f"\n下载完成！总共下载了 {total_citations} 篇引文数据到 {OUTPUT_FILE}")
    else:
        print(f"\n操作完成，但未下载任何引文。请检查PAPER_ID或错误信息。")


if __name__ == "__main__":
    get_citations()