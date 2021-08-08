import requests
import json
import re
from gcd_issues import gcd_issue_ids

# DB Schema: https://miro.com/app/board/o9J_l4VnWWE=/
# Combine data from multiple sources to create BMR database records representing issues

def get_gcd_cover(gcd_id):
  req = requests.get(f'https://www.comics.org/issue/{gcd_id}').text
  cover_regex = "https://files1\.comics\.org//img/gcd/covers_by_id/.*\.jpg"
  cover_url = re.search(cover_regex, req, re.M)
  # Change width to 400px here or on front-end?
  # cover_url = re.sub("\/w\d{3}\/", "/w400/", cover_url)
  return cover_url.groups() if cover_url else None

def format_bmr_issue(gb_issue, gcd_issue):
  try:
    issue = dict(
      isbn = gcd_issue['isbn'],
      gcd_id = gcd_issue['id'],
      gcd_series_id = gcd_issue['series_id'],
      gb_id = gb_issue['id'],
      title=gb_issue['volumeInfo']['title'],
      subtitle=gb_issue['volumeInfo'].get('subtitle'),
      description=gb_issue['volumeInfo'].get('description'),
      publisher=gb_issue['volumeInfo'].get('publisher'),
      published_date=gb_issue['volumeInfo'].get('publishedDate'),
      mature_content= not (gb_issue['volumeInfo']['maturityRating'] == "NOT_MATURE"),
      language=gb_issue['volumeInfo'].get('language'),
      page_count=gb_issue['volumeInfo'].get('pageCount'),
      thumbnail_url=gb_issue['volumeInfo'].get('imageLinks', {}).get('thumbnail'),
      reader_link=gb_issue['accessInfo']['webReaderLink'] if gb_issue['accessInfo']['accessViewStatus'] != "NONE" else None,
      snippet=gb_issue.get('searchInfo', {}).get('textSnippet'),
      cover_url=None,
      # Represented as relationships in database
      genres = gb_issue['volumeInfo'].get('categories', [])
    )
  except KeyError as e:
    print(f'KeyError for ISBN {gcd_issue["isbn"]} - reason: {e}')
    return None

  issue['cover_url'] = get_gcd_cover(issue['gcd_id'])
  return issue

FETCH_LIMIT = 2
def get_issues():
  bmr_issues = []
  for issue in gcd_issue_ids[:FETCH_LIMIT]: 
    # Some issues have multiple ISBNs with semi-colons as a delimiter
    issue['isbn'] = re.search("[\d,-]*[^;]", issue['isbn']).group().replace('-','');
    isbn = issue['isbn']
    print(f'Fetching Google Books records for ISBN {isbn}...')
    req = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')
    if not req.json().get('items', None):
      print(f'No Google Books records for ISBN {isbn}.')
      continue
    # Sometimes there are duplicate records for the same ISBN. For now, just grab the first.
    gb_issue = req.json()['items'][0]
    bmr_issue = format_bmr_issue(gb_issue=gb_issue, gcd_issue=issue)
    if bmr_issue: 
      bmr_issues.append(bmr_issue)
  return bmr_issues

ISSUE_FIELDS = ['gcd_id', 'gb_id', 'gcd_series_id', 'title', 'subtitle', 'description', 'snippet', 'publisher', 'published_date', 'maturity_rating', 'language', 'isbn', 'page_count', 'thumbnail_url', 'cover_url']
def generate_issue_seed_data(issues):
  f = open("issue_seeds.py", "a")
  sql_start = 'INSERT into bmr_isses ('
  for field in ISSUE_FIELDS:
    sql_start += f'{field},'
  sql_start = sql_start[:-1] + ") VALUES ("
  f.write(sql_start)
  f.close()
  for issue in issues:
      f = open("issue_seeds.py", "a")
      values = [issue.get(f) for f in ISSUE_FIELDS]
      # Add quotes to string frields
      values = [f'"{v}"' if isinstance(v, str) else str(v) for v in values]
      field_text = ", ".join(values)
      f.write(json.dumps(f'({field_text})'))
      f.close()
  # TO DO - handle storing genres and creators during this loop or in subsequent loops
issues = get_issues()

generate_issue_seed_data(issues)