import json
import time
import uuid

from gevent import monkey

monkey.patch_all()
import gevent
import requests as requests
from bs4 import BeautifulSoup

base_url = 'https://baza-otvetov.ru'
data = []


def get_wrong_answers(question: dict):
    if question['link'] is None:
        return
    fq_soup = BeautifulSoup(requests.get(question['link']).text, 'lxml')
    fq_soup = fq_soup.find('div', class_='similar-qs')
    arr = [ans.text.replace('Ответ: ', '').replace('\"', '') for ans in fq_soup.find_all('h6') if
           not ans.text.startswith('Ответы для викторин')]
    question.pop('link')
    question.update({'wrong_answers': arr})
    data.append(question)


def parse_page(pg_soup, category_name):
    for question in pg_soup.find_all('tr'):
        if len(question.find_all('td')) == 0:
            continue
        question_id = str(uuid.uuid4())

        available_answers = pg_soup.find('div', class_='q-list__quiz-answers')
        wrong_answers = None
        link = None
        if available_answers:
            wrong_answers = available_answers.text.replace('Ответы для викторин: ', '').strip().split(', ')
        else:
            link = base_url + question.find_all('td')[1].a['href']

        data.append(dict(question_id=question_id,
                         category_name=category_name,
                         question=question.find_all('td')[1].a.text.replace('\n', '').replace('\"', ''),
                         answer=question.find_all('td')[2].text.replace('\"', ''),
                         link=link,
                         wrong_answers=wrong_answers))


def parse_category(category_id):
    response = requests.get(base_url + f'/categories/view/{category_id}')
    soup = BeautifulSoup(response.text, 'lxml')
    category_name = soup.find('h2', class_='page-title')
    paginator = 0
    soups = []
    category_start = time.time()
    while response.status_code == 200:
        paginator = paginator + 10
        response = requests.get(base_url + f'/categories/view/{category_id}/{paginator}')
        soups.append(BeautifulSoup(response.text, 'lxml'))

    jobs = [gevent.spawn(parse_page, soup, category_name.text) for _soup in soups]
    gevent.wait(jobs)
    category_end = time.time()
    print(category_id, ":category parsed: ", category_end - category_start)


def parse_all():
    all_start = time.time()
    for i in range(1, 30):
        if i == 24:
            continue
        parse_category(i)
        # f = open('result2.json', 'w')
        # result = dict(data=data)
        # f.write(json.dumps(result, indent=4, ensure_ascii=False))
        # f.close()

    print('start parse wrong answers:')
    futures = [gevent.spawn(get_wrong_answers, question) for question in data]
    gevent.wait(futures)

    f = open('result2.json', 'w')
    f.write(json.dumps(dict(data=data), indent=4, ensure_ascii=False))
    f.close()
    all_end = time.time()
    print("all parsed: ", all_end - all_start)
