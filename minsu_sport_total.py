import re
import urllib.parse
from urllib.request import Request, urlopen
import bs4
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime



def get_weather_info(day):
    weathers = soup.select('tbody > tr > td')
    for weather in weathers:
        strong_tag = weather.select_one('strong.num')
        if strong_tag is None:
            continue

        day_class = strong_tag['class']
        weather_day = int(strong_tag.text)
        condition = weather.select_one('span.blind').text
        temps = weather.select('span.temper > span.text')
        temp_high = temps[0].text.replace('°', '도')
        temp_low = temps[1].text.replace('°', '도')
        rainfall = weather.select_one('span.amount').text.split()[-1]

        # 현재 달의 특정 날짜의 날씨 정보 반환
        if 'num' in day_class and 'next' not in day_class and 'prev' not in day_class and weather_day == day:
            return [condition, temp_high, temp_low, rainfall]

    return None

# 날짜와 종목을 사용자로부터 입력받기
day = input("원하는 경기일자가 언제인가요? (예: 2024-04-03): ")
sport = input("어떤 종목의 경기를 보고 싶은가요? : ")


# 문자열을 datetime 객체로 변환
date_obj = datetime.strptime(day, "%Y-%m-%d")

# 원하는 형식으로 변환
day = date_obj.strftime("%Y년 %m월 %d일")



# 정규 표현식으로 월과 일을 추출
month_match = re.search(r'(\d{1,2})월', day)
day_match = re.search(r'(\d{1,2})일', day)

if month_match:
    wanted_month = month_match.group(1)
else:
    raise ValueError("월을 찾을 수 없습니다.")

if day_match:
    wanted_day = day_match.group(1)
else:
    raise ValueError("일을 찾을 수 없습니다.")

# 경기 일정 검색 및 파싱
keyword = f"{day} {sport} 경기일정"
url = f"https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bjA5&qvt=0&query={urllib.parse.quote(keyword)}"
response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # 경기팀 정보를 저장할 리스트
    teams = []
    # 경기시간 정보를 저장할 리스트
    match_times = []
    # 경기 장소 정보를 저장할 리스트
    locations = []

    # 경기팀 정보가 포함된 요소를 찾기
    all_spans = soup.find_all("span", {"class": "txt_name txt_pit"})
    for span in all_spans:
        a_tag = span.find("a")
        if a_tag:
            team_name = a_tag.get_text(strip=True)
            teams.append(team_name)

    # 경기시간 정보가 포함된 요소를 찾기
    match_time_divs = soup.find_all("span", {"class": "bg_none"})
    for match_time_div in match_time_divs:
        match_time_text = match_time_div.get_text(strip=True)
        match_times.append(match_time_text)

    # 경기 장소 정보가 포함된 요소를 찾기
    location_tds = soup.find_all("td", {"class": "place"})
    for location_td in location_tds:
        location_text = location_td.get_text(strip=True)
        locations.append(location_text)

    # 홈 구장을 기준으로 홈팀을 결정하기 위한 사전 정의된 딕셔너리
    home_grounds = {
        "사직": "롯데",
        "잠실": ["LG", "두산"],
        "고척": "키움",
        "문학": "SSG",
        "수원": "KT",
        "대구": "삼성",
        "창원": "NC",
        "광주": "KIA",
        "대전": "한화",
         # 추가 예시
    }

    home_teams = []
    away_teams = []

    # 팀과 장소 정보를 매칭하여 홈팀과 원정팀 구분
    for i in range(0, len(teams), 2):
        if i // 2 < len(locations):
            location = locations[i // 2]
            home_team = home_grounds.get(location, None)
            if home_team:
                if isinstance(home_team, list):
                    if teams[i] in home_team:
                        home_teams.append(teams[i])
                        away_teams.append(teams[i + 1])
                    else:
                        home_teams.append(teams[i + 1])
                        away_teams.append(teams[i])
                else:
                    if teams[i] == home_team:
                        home_teams.append(teams[i])
                        away_teams.append(teams[i + 1])
                    else:
                        home_teams.append(teams[i + 1])
                        away_teams.append(teams[i])
            else:
                home_teams.append(teams[i])
                away_teams.append(teams[i + 1])
        else:
            home_teams.append(teams[i])
            away_teams.append(teams[i + 1])

    # 데이터프레임 생성
    data = {
        "홈팀": home_teams,
        "원정팀": away_teams,
        "경기시간": match_times[:len(home_teams)],
        "경기장소": locations[:len(home_teams)]
    }
    df = pd.DataFrame(data)

    # 날씨 정보를 저장할 리스트
    weather_descriptions = []

    # 경기 장소별로 날씨 정보 조회 및 추가
    for location in df['경기장소']:
        search_location = "인천" if location == "문학" else location

        enc_location = urllib.parse.quote(f"{day} {search_location} 날씨")
        url = f'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query={enc_location}'
        
        req = Request(url)
        page = urlopen(req)
        html = page.read()
        soup = bs4.BeautifulSoup(html, 'html5lib')
        
        weather_info = get_weather_info(int(wanted_day))

        if weather_info:
            weather_desc, max_temp, min_temp, precipitation = weather_info
            precipitation_text = '없습니다' if precipitation == '-' else precipitation

            # 강수량 분석
            if precipitation != '-' and precipitation != '없습니다':
                try:
                    precipitation_value = float(precipitation.replace('mm', ''))
                except ValueError:
                    precipitation_value = 0.0
            else:
                precipitation_value = 0.0

            precipitation_warning = ''
            if precipitation_value >= 10:
                precipitation_warning = "폭우로 우천 취소될 가능성 높음"
            # 출력할 문장 형식화
            formatted_date = f"{int(wanted_month)}월 {int(wanted_day)}일"
            weather_description = f"{weather_desc} 강수량은 {precipitation_text}. {precipitation_warning}"
        else:
            weather_description = "N/A"        

        weather_descriptions.append(weather_description)

    # 날씨 정보를 데이터프레임에 추가
    df['날씨'] = weather_descriptions

    pd.set_option('display.unicode.east_asian_width', True)

    # 결과 출력
    if not df.empty:
        print(df)
    else:
        print("경기팀 정보, 경기시간 정보 또는 경기 장소 정보를 찾을 수 없습니다.")
else:
    print(f"웹페이지를 가져오는 데 실패했습니다. 상태 코드: {response.status_code}")



