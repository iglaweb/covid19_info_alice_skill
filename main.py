# -*- coding: utf-8 -*-
"""Module documentation goes here
   and here
   and ...
"""
import json
import logging
import site

import os

import virus_utils

from bottle import Bottle, request

site.addsitedir('/usr/local/lib/python3.6/site-packages')
site.addsitedir('/usr/local/lib/python3.6/dist-packages')

app = Bottle(False)


def run_main():
    print(virus_utils.get_total_rus())

    stat = virus_utils.find_country_by_name_rus('russia')
    print(stat)

    confirmed = get_confirmed()
    print(f'Confirmed: {confirmed}')

    cases = get_cases()
    print(f'Cases: {cases}')

    virus_data_ = virus_utils.obtain_virus_data()
    print(virus_data_)

    resp = virus_utils.find_country_by_name('china')
    print(resp)


@app.get('/test')
def api():
    run_main()
    return "Completed."


@app.get('/total')
def get_total():
    return virus_utils.get_total_rus()


@app.get("/")
def redirect_to_app():
    cwd = os.getcwd()
    return cwd


@app.get('/get_cases')
def get_cases():
    total_cases = virus_utils.get_total_cases()
    return str(total_cases)


@app.get('/get_confirmed')
def get_confirmed():
    total_confirmed = virus_utils.get_total_confirmed()
    return str(total_confirmed)


@app.get('/get_country')
def get_country():
    """Get country by get parameter name"""
    name = request.query.name
    return virus_utils.find_country_by_name_rus(name)


if __name__ == '__main__':
    run_main()

# Session storage
sessionStorage = {}


@app.post('/dialog_virus_stats')
def yandex_dialog_virus_stats():
    """Dialog registered in Alisa catalog"""
    body = request.body.read()
    body = json.loads(body)
    logging.info('Request: %r', body)

    response = {
        "version": body['version'],
        "session": body['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog_virus_stats(body, response)
    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


possible_answers_total_stats_yadialog = [
    'общая',
    'общую',
    'общая статистика',
    'общую статистику',
    'всего',
    'статистика',
    'в мире',
    'мир'
]

possible_answers_help_yadialog = [
    'помощь',
    'помоги',
    'что ты умеешь'
]

possible_answers_tips_yadialog = [
    'рекомендации',
    'рекомендации для населения',
    'меры предосторожности',
    'правила предосторожности',
    'инструкции'
]

possible_answers_incubation_yadialog = [
    'сколько длится инкубационный период?',
    'инкубационный период'
]

possible_answers_about_virus = [
    'что такое короновирус?',
    'что такое'
]

l18n_str_help = 'Я могу рассказать про статистику по заболеваемости короновирусом в мире.' \
                ' Для этого нужно просто сказать "Общая".' \
                ' Если вам интереснее статистика по стране,' \
                ' скажите название страны, например "Россия".'

l18n_str_virus_about = 'Коронавирус — большое семейство вирусов, которыми могут заражаться как животные, так и человек.' \
                       ' Некоторые из них заражают человека и способны вызывать различные болезни,' \
                       ' от обычной простуды до более серьезных состояний,' \
                       ' таких как ближневосточный респираторный синдром (БВРС)' \
                       ' и тяжелый острый респираторный синдром (ТОРС).'

l18n_str_virus_symptoms = 'Симптомы инфекции 2019-nCoV, как и других респираторных заболеваний,' \
                          ' могут быть умеренными и включать в себя насморк,' \
                          ' боль в горле, кашель и повышение температуры.' \
                          ' У некоторых людей она может протекать более тяжело и приводить к пневмонии ' \
                          'или затрудненному дыханию. В более редких случаях болезнь может иметь летальный исход. '

l18_str_virus_tips = 'Регулярно мойте руки.' \
                     ' Соблюдайте правила респираторной гигиены.' \
                     ' Держитесь от людей на расстоянии как минимум 1 метра,' \
                     ' особенно если у них кашель, насморк и повышенная температура. ' \
                     'По возможности, не трогайте руками глаза, нос и рот. ' \
                     'При повышении температуры, появлении кашля и затруднении дыхания' \
                     ' как можно быстрее обращайтесь за медицинской помощью. ' \
                     'Не употребляйте в пищу сырые или не прошедшие' \
                     ' надлежащую термическую обработку продукты животного происхождения'

l18n_str_incubation_period = 'Инкубационный период – это период времени между заражением' \
                             ' и появлением клинических симптомов болезни.' \
                             ' По текущим оценкам, продолжительность инкубационного периода составляет' \
                             ' от 1 до 14 дней со средним значением порядка 5–6 дней. '


# Функция для непосредственной обработки диалога.
def handle_dialog_virus_stats(req, res):
    user_id = req['session']['user_id']

    if req['session']['new']:
        # new user
        # init session and welcome
        sessionStorage[user_id] = {
            'suggests': [
                'Помощь',
                "В мире",
                'Россия',
                'Китай'
            ]
        }

        res['response'][
            'text'] = 'Привет! Я могу показать общую статистику по заболеваемости в мире или только по стране.' \
                      ' Для подробных инструкций скажите "Помощь".'
        res['response']['buttons'] = get_virus_suggests(user_id)
        return

    # Обрабатываем ответ пользователя.
    original_cmd = req['request']['original_utterance'].lower()
    if original_cmd in possible_answers_tips_yadialog:
        res['response']['text'] = l18_str_virus_tips
        res['response']['buttons'] = get_virus_suggests(user_id, True)
        return

    # incubation
    if original_cmd in possible_answers_incubation_yadialog:
        res['response']['text'] = l18n_str_incubation_period
        res['response']['buttons'] = get_virus_suggests(user_id, True)
        return

    # what is virus?
    if original_cmd in possible_answers_about_virus:
        res['response']['text'] = l18n_str_virus_about
        res['response']['buttons'] = get_virus_suggests(user_id, True)
        return

    # search for help
    if original_cmd in possible_answers_help_yadialog:
        res['response']['text'] = l18n_str_help
        res['response']['buttons'] = get_virus_suggests(user_id)
        return

    tokens = req['request']['nlu']['tokens']
    share_common_elements = any(x in tokens for x in possible_answers_total_stats_yadialog)

    # check if total request
    if share_common_elements or original_cmd in possible_answers_total_stats_yadialog:
        res['response']['text'] = virus_utils.get_total_rus()
        res['response']['buttons'] = get_virus_suggests(user_id)
        return

    # look for geo entity
    entities = req['request']['nlu']['entities']
    searched_country = original_cmd
    if entities is not None and len(entities) > 0:
        for item in entities:
            if item['type'] == 'YANDEX.GEO':
                searched_country = item['value']['country']
                if virus_utils.is_country_supported(searched_country):
                    break

    # search for country
    country_stat = virus_utils.find_country_by_name_rus(searched_country)
    res['response']['text'] = country_stat
    res['response']['buttons'] = get_virus_suggests(user_id)


# Функция возвращает две подсказки для ответа.
def get_virus_suggests(user_id, show_help: bool = False):
    session = sessionStorage[user_id]
    # if help requested show single button, otherwise actions
    if show_help:
        sessions_suggests = session['suggests'][:1]
    else:
        sessions_suggests = session['suggests'][1:]

    suggests = [
        {'title': suggest, 'hide': True}
        for suggest in sessions_suggests
    ]
    return suggests
