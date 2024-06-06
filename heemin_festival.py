import urllib.parse
from urllib.request import Request, urlopen
import bs4
import datetime
import sqlite3

def get_weather(date_obj, now_location):
    formatted_date = date_obj.strftime("%Y년 %m월 %d일")
    location = formatted_date+now_location+"날씨"

    original_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    selected_date = original_date.strftime('%m/%d')

    enc_location = urllib.parse.quote(location)
    url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=' + enc_location
    # print(url)
    req = Request(url)
    page = urlopen(req)
    html = page.read()
    soup = bs4.BeautifulSoup(html, 'html5lib')


    weathers = soup.select('tbody > tr > td')

    def get_weather_dict(weathers, current_month):
        weather_dict = {}
        for weather in weathers:
            strong_tag = weather.select_one('strong.num, strong.num prev, strong.num next')
            if strong_tag is None:
                continue

            day_class = strong_tag['class']  # 'prev', 'num', 'next' 중 하나
            day = int(strong_tag.text)  # 날짜를 정수로 변환
            condition = weather.select_one('span.blind').text
            temps = weather.select('span.temper > span.text')
            temp_high = temps[0].text
            temp_low = temps[1].text
            rainfall = weather.select_one('span.amount').text.split()[-1]

            if 'prev' in day_class:
                month = (int(current_month) - 2) % 12 + 1
            elif 'next' in day_class:
                month = int(current_month) % 12 + 1
            else:
                month = current_month
                

            weather_dict[f'{month:02}/{day:02}'] = [condition, temp_high, temp_low, rainfall]

        return weather_dict


    current_month = date_obj.month
    weather_dict = get_weather_dict(weathers, current_month)

    if selected_date in weather_dict:
        weather_info = weather_dict[selected_date]
        weather_desc = weather_info[0]
        max_temp = weather_info[1].replace('°', '도')
        min_temp = weather_info[2].replace('°', '도')
        precipitation = weather_info[3]
        
        # 강수량 정보를 포맷
        if precipitation == '-':
            precipitation_text = '없습니다'
        else:
            precipitation_text = f'{precipitation}'

        month, day = selected_date.split('/')
        month = str(int(month))  # 월에서 앞의 0을 제거
        day = str(int(day))
        # 출력할 문장 형식화
        output = f"{now_location}에는 {weather_desc}, 최고기온은 {max_temp}, 최저기온은 {min_temp}, 강수량은 {precipitation_text}."
        print(output)
    else:
        print(f"{formatted_date}에 대한 날씨 정보가 없습니다.")



# 데이터베이스 연결 sql
def get_festival(name, date):
    conn = sqlite3.connect('eventmate.db')
    cursor = conn.cursor()
    
    sql = """
        SELECT F.festival_name, F.location, F.start_date, F.end_date, F.description, F.provider_name
        FROM USER U
        JOIN LIKE L ON U.user_id = L.user_id
        JOIN FESTIVAL F ON (F.festival_name LIKE '%' || L.like || '%' OR F.description LIKE '%' || L.like || '%')
        JOIN DISLIKE D ON U.user_id = D.user_id
        WHERE U.name = ?
        AND (D.dislike IS NULL OR F.festival_name NOT LIKE '%' || D.dislike || '%')
        AND (? <= end_date)
        ORDER BY start_date LIMIT 5;
    """


    cursor.execute(sql, (name, date))
    result = cursor.fetchall()
    
    conn.close()
    return result if result else None

user_name = str(input("사용자 이름 입력 : "))

date_str = str(input("원하는 축제일자가 언제인가요? (예: 2024-04-03) : "))

# 문자열을 datetime 객체로 변환
date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")


for place in get_festival(user_name, date_str):
    print(f'페스티벌 이름:{place[0]}, 장소:{place[1]}, 시작일:{place[2]}, 마감일:{place[3]}')
    print(f'설명:{place[4]}')
    # print(place[5])
    get_weather(date_obj, place[5])
    print()







