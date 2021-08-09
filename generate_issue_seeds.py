# Combine data from multiple sources to create BMR database records representing issues

import requests
import json
import re
from gcd_issues import gcd_issue_ids

ISSUE_SEEDS_FILE = "issue_seeds.sql"


def get_issue_details(issue):
  # Gather all data required to create an issue record, including data from Google Books and a cover image url fetched from the Grand Comic Database website.

  def get_gcd_cover(gcd_id):
    req = requests.get(f'https://www.comics.org/issue/{gcd_id}').text
    cover_regex = "https://files1\.comics\.org//img/gcd/covers_by_id/.*\.jpg"
    cover_url = re.search(cover_regex, req, re.M)
    # Change width to 400px here or on front-end?
    # cover_url = re.sub("\/w\d{3}\/", "/w400/", cover_url)
    return cover_url.group() if cover_url else None

  # Some issues have multiple ISBNs with semi-colons as a delimiter. For now, just save the first.
  issue['isbn'] = re.search("[\d,-]*[^;]", issue['isbn']).group().replace('-','');
  isbn = issue['isbn']

  print(f'Fetching Google Books records for ISBN {isbn}...')
  req = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}')
  if not req.json().get('items', None):
    print(f'No Google Books records for ISBN {isbn}.')

  # Sometimes there are duplicate records for the same ISBN. For now, just grab the first.
  gb_issue = req.json()['items'][0]
  gb_issue['cover_url'] = get_gcd_cover(issue['id']) # TO DO - change this to "gcd_id" in the export

  bmr_issue = format_bmr_issue(gb_issue=gb_issue, gcd_issue=issue)

  return bmr_issue


def format_bmr_issue(gb_issue, gcd_issue):
  def format_published_date(published_date):
    if published_date:
      # No month? Set to Jan.
      if re.search('\d{4}$', published_date):
        published_date += "01"
      # No day? Set to 1st.
      if re.search('\d{4}-\d{2}$', published_date):
        published_date += "-01"
      # Don't include malformed dates
      if not re.search('\d{4}-\d{2}-\d{2}$', published_date):
        published_date = None
    return published_date

  try:
    volume = gb_issue['volumeInfo']
    access = gb_issue['accessInfo']
    published_date = format_published_date(volume.get('publishedDate'))
    return dict(
      isbn = gcd_issue['isbn'],
      gcd_id = gcd_issue['id'],
      gcd_series_id = gcd_issue['series_id'],
      gb_id = gb_issue['id'],
      title = volume['title'],
      subtitle = volume.get('subtitle'),
      description = volume.get('description'),
      publisher = volume.get('publisher'),
      published_date = published_date,
      mature = not (volume['maturityRating'] == "NOT_MATURE"),
      language = volume.get('language'),
      page_count = volume.get('pageCount'),
      thumbnail_url = volume.get('imageLinks', {}).get('thumbnail'),
      reader_link = access['webReaderLink'] if access['accessViewStatus'] != "NONE" else None,
      snippet = gb_issue.get('searchInfo', {}).get('textSnippet'),
      cover_url = None,
      # Represented as relationships in database
      genres = gb_issue['volumeInfo'].get('categories', [])
    )
  except KeyError as e:
    print(f'KeyError for ISBN {gcd_issue["isbn"]} - reason: {e}')
    return None


def generate_issue_seed_data():
  # Create sql file to seed BMR database with issue records based off a list of dicts containing each issue's GCD id, GCD series id, and ISBN.

  ISSUE_FIELDS = ['gcd_id', 'gb_id', 'gcd_series_id', 'title', 'subtitle', 'description', 'snippet', 'publisher', 'published_date', 'mature', 'language', 'isbn', 'page_count', 'thumbnail_url', 'cover_url']
  ISSUE_TABLE_NAME = "bmr_issue"
  FETCH_LIMIT = 2

  def write_sql_start():
    f = open(ISSUE_SEEDS_FILE, "w")
    sql_start = f'INSERT into {ISSUE_TABLE_NAME} ('
    for field in ISSUE_FIELDS:
      sql_start += f'{field},'
    sql_start = sql_start[:-1] + ") VALUES "
    f.write(sql_start)
    f.close()

  def create_issue_insert_statement(issue, is_last):
    values = [issue.get(f) for f in ISSUE_FIELDS]
    # Add quotes to string fields and swap None with null
    for i,v in enumerate(values):
      if isinstance(v, str): 
        values[i] = json.dumps(v)  
      elif isinstance(v, bool): 
        values[i] = str(int(v))
      elif v is None: 
        values[i] = 'null'
      else: values[i] = str(v)

    # Replace double dashes that conflict with SQL's commenting syntax
    field_text = ", ".join(values).replace("--", "-").replace("'", "''")
    delimiter = ',' if is_last else ';'
    return f'({field_text}){delimiter}'
  
  def write_issue(issue, is_last):
    f = open(ISSUE_SEEDS_FILE, "a")
    insert_statement = create_issue_insert_statement(issue, is_last)
    f.write(insert_statement)
    f.close()

  write_sql_start()
  issues =  gcd_issue_ids[:FETCH_LIMIT]
  for idx, issue in enumerate(issues):
    issue = get_issue_details(issue)
    write_issue(issue, idx < (len(issues) - 1))

  # TO DO - handle storing genres and creators during this loop or in subsequent loops

# -------------------------------------------------------

def run():
  generate_issue_seed_data()
  print(f'Seeding complete! See file: {ISSUE_SEEDS_FILE}')