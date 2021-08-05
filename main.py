import requests

# Combine data from multiple sources to create BMR database records representing issues

# bmr_issue_base = dict(
#   id=None,#(int)
#   gcd_id=None,#(int)
#   title=None,#(str)
#   subtitle=None,#(str)
#   description=None,#(str)
#   snippet=None,#(str)
#   publisher=None,#(str)
#   published_date=None,#(datetime)
#   maturity_rating=None,#(string)
#   language=None,#(tinytext)
#   isbn=None,#(int)
#   page_count=None,#(int)
#   thumbnail_url=None,#(text)
#   cover_url=None#(text)
# )

# Make another request for issue by GB id to get categories?

# For ISBNS, split on semi-colon and get first item (some have multiple) and remove all non-numerical characters

def format_bmr_issue(gb_issue, gcd_issue):
  try:
    issue = dict(
      isbn = gcd_issue['isbn'],
      gcd_id = gcd_issue['id'],
      gb_id = gb_issue['id'],
      title=gb_issue['volumeInfo']['title'],
      subtitle=gb_issue['volumeInfo'].get('subtitle', None),
      description=gb_issue['volumeInfo'].get('description', None),
      publisher=gb_issue['volumeInfo'].get('publisher', None),
      published_date=gb_issue['volumeInfo']['publishedDate'],
      mature_content= not (gb_issue['volumeInfo']['maturityRating'] == "NOT_MATURE"),
      language=gb_issue['volumeInfo']['language'],
      page_count=gb_issue['volumeInfo']['pageCount'],
      thumbnail_url=gb_issue['volumeInfo'].get('imageLinks', {}).get('thumbnail', None),
      reader_link=gb_issue['accessInfo']['webReaderLink'] if gb_issue['accessInfo']['accessViewStatus'] != "NONE" else None,
      snippet=gb_issue.get('searchInfo', {}).get('textSnippet', None),
      cover_url=None,
      # Represented as relationships in database
      genres=gb_issue['volumeInfo'].get(['genres']),
    )
    return issue
  except KeyError as e:
    print(gcd_issue['isbn'])
    print(f'KeyError for ISBN {gcd_issue["isbn"]} - reason: {e}')

def get_issues():
  gcd_issues = [
    dict(isbn='0930193466', id=123),
    dict(isbn='1302914790', id=124)
  ]
  bmr_issues = []
  for issue in gcd_issues: 
    req = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}".format(isbn=issue['isbn']))
    if not req.json()['items']:
      continue
    # Sometimes there are duplicate records for the same ISBN. For now, just grab the first.
    gb_issue = req.json()['items'][0]
    print(gb_issue)
    bmr_issue = format_bmr_issue(gb_issue=gb_issue, gcd_issue=issue)
    if bmr_issue: bmr_issues.append(bmr_issue)
  return bmr_issues

# unpac dict to make insert statement

print(get_issues())