# 라이브러리 불러오기

import pandas as pd
import numpy as np
import datetime
from keras.models import load_model
from haversine import haversine
from urllib.parse import quote
import streamlit as st
from streamlit_folium import st_folium
import folium
import branca
from geopy.geocoders import Nominatim
import ssl

from streamlit_calendar import calendar


# 네이버 api
import json
import urllib
from urllib.request import Request, urlopen
import plotly.express as px

option = ''


def get_optimal_route(start, goal, option=option):
    client_id = 'fy9m99zzte'
    client_secret = 'gtOMi8OG2TbOuRhsfthH0dPV2WAEP8A2DAjTAW7x'

    url = f"https://naveropenapi.apigw.ntruss.com/map-direction-15/v1/driving?start={start[0]},{start[1]}&goal={goal[0]},{goal[1]}&option={option}"

    request = urllib.request.Request(url)
    request.add_header('X-NCP-APIGW-API-KEY-ID', client_id)
    request.add_header('X-NCP-APIGW-API-KEY', client_secret)

    response = urllib.request.urlopen(request)
    res = response.getcode()

    if res == 200:
        response_body = response.read().decode('utf-8')
        return json.loads(response_body)
    else:
        print('ERROR')


def results(results):
    lati_long = []
    japho = results['route']['traoptimal'][0]['path']
    for coord in japho:
        latitude, longitude = coord[1], coord[0]
        lati_long.append([latitude, longitude])
    return lati_long


# geocoding : 거리주소 -> 위도/경도 변환 함수
# Nominatim 파라미터 : user_agent = 'South Korea', timeout=None
# 리턴 변수(위도,경도) : lati, long
def geocoding(address):
    geolocoder = Nominatim(user_agent = 'South Korea', timeout=None)
    geo = geolocoder.geocode(address)
    lati = geo.latitude
    longit = geo.longitude
    return lati, longit

# -------------------------------------
#community_data = pd.read_csv('/content/drive/MyDrive/빅프csv/beebe.csv', encoding="cp949")
address = '서울특별시'
## 오늘 날짜
now_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)
now_date2 = datetime.datetime.strptime(now_date.strftime("%Y-%m-%d"), "%Y-%m-%d")

## 2024년 최소 날짜, 최대 날짜
first_date = pd.to_datetime("2024-01-01")
last_date = pd.to_datetime("2024-12-31")

st.set_page_config(layout="wide")

# tabs 만들기
tab1, tab2= st.tabs(['Bee119 신고 출동', '양봉장 밀원 분포지도'])

# tab1 내용물 구성하기
with tab1:

    # 제목 넣기
    st.markdown("## Bee119 신고 출동")

    # 시간 정보 가져오기
    now_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)


    # 정보 널기
    #st.markdown("#### 출동 정보")

    ## --------------------

    col110, col111, col112, col113 = st.columns([0.12, 0.28, 0.12, 0.28])
    with col110:
        st.info('신고일')
    with col111:
        input_date = st.date_input('날짜정보',label_visibility='collapsed')
    with col112:
        st.info('신고시간')
    with col113:
        input_time = st.time_input('시간정보',label_visibility='collapsed')


    ## -------------------------------------------------------------------------------------

    col120, col121, col122, col123 = st.columns([0.12, 0.28, 0.12, 0.28])
    with col120:
        st.info('사고위치')
    with col121:
        address1 = st.text_input('주소 텍스트 입력',value='서울특별시',label_visibility='collapsed')
    with col122:
        st.info('관할소방서')
    with col123:
        phonenum = st.text_input('소방서입력',value='소방서',label_visibility='collapsed')

    with st.form(key='tab1_first'):

        ### 버튼 생성
        if st.form_submit_button(label='위치조회'):

            #### 거리주소 -> 위도/경도 변환 함수 호출
            lati, longit = geocoding(address)

            display_df = pd.read_csv('/content/drive/MyDrive/빅프csv/양봉qhd.csv',encoding="cp949")
            display_df2 = pd.read_csv('/content/drive/MyDrive/빅프csv/꽃지도.csv',encoding="cp949")

            distance2 = []

            for idx1, row1 in display_df.iterrows():
                flower = '잡화,'
                for idx2, row2 in display_df2.iterrows():
                    rounded_distance = round(haversine((row2['위도'], row2['경도']), (row1['위도'], row1['경도']), unit='km'), 2)

                    if rounded_distance <= 2:
                        flower += row2['꽃'] + ','

                flowers = [i.strip() for i in flower.rstrip(',').split(',')]
                # 중복 제거
                unique_flowers = list(set(flowers))
                unique_flowers_join = ', '.join(unique_flowers)
                distance2.append(unique_flowers_join)

            display_df['근처 꽃'] = distance2

            distance = []
            patient = (lati, longit)

            for idx, row in display_df.iterrows():
                distance.append(round(haversine((row['위도'], row['경도']), patient, unit='km'), 2))

            display_df['거리'] = distance
            display_df['거리구분'] = pd.cut(display_df['거리'], bins=[-1, 2, 5, 10, 100],
                                 labels=['2km이내', '5km이내', '10km이내', '10km이상'])

            display_df = display_df[display_df.columns].sort_values(['거리구분', '거리'], ascending=[True, True])
            display_df.reset_index(drop=True, inplace=True)
            short_load = display_df[['위도','경도']]

            display_dff = display_df.drop(['위도','경도'],axis=1)

            if display_dff['거리'].iloc[0] <= 10 :
                st.markdown(f"### 예상되는 분봉 장소는 {display_dff['이름'].iloc[0]}입니다")

            #### 사고위치
            with st.expander("도시양봉맵", expanded=True):
                m = folium.Map(location=[lati,longit], zoom_start=12)
                icon = folium.Icon(color="red")
                html = """<!DOCTYPE html>
                    <html>
                        <table style="height: 126px; width: 330px;"> <tbody> <tr>
                            <td style="background-color: #FD5252;">
                            <div style="color: #ffffff;text-align:center;">벌 사고 발생 위치</div></td>
                            <td style="width: 230px;background-color: #C5C5C3;">{}</td>""".format(address)+"""</tr>
                        </tbody> </table> </html> """
                iframe = branca.element.IFrame(html=html, width=350, height=150)
                popup_text = folium.Popup(iframe,parse_html=True)
                folium.Marker(location=[lati , longit], popup=popup_text, tooltip="사고 발생 위치 : "+address, icon=icon).add_to(m)


                ###### 양봉지도

                for idx, row in display_df[:].iterrows():
                    html = """<!DOCTYPE html>
                    <html>
                        <table style="height: 126px; width: 330px;"> <tbody> <tr>
                            <td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">양봉지명</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['이름'])+"""</tr>
                            <tr><td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">주소</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['주소'])+"""</tr>
                            <tr><td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">근처 꽃</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['근처 꽃'])+"""</tr>
                            <tr><td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">연락처</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['연락처'])+"""</tr>
                        </tbody> </table> </html> """

                    iframe = branca.element.IFrame(html=html, width=360, height=200)
                    popup_text = folium.Popup(iframe,parse_html=True)
                    icon = folium.Icon(icon="forumbee",color="orange",prefix="fa")
                    folium.Marker(location=[row['위도'], row['경도']],
                                  popup=popup_text, tooltip=row['이름'], icon=icon).add_to(m)

                # 꽃지도
                for idx, row in display_df2[:].iterrows():
                    html = """<!DOCTYPE html>
                    <html>
                        <table style="height: 126px; width: 330px;"> <tbody> <tr>
                            <td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">이름</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['이름'])+"""</tr>
                            <tr><td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">주소</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['주소'])+"""</tr>
                            <tr><td style="background-color: #F2952F;">
                            <div style="color: #ffffff;text-align:center;">꽃</div></td>
                            <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['꽃'])+"""</tr>
                        </tbody> </table> </html> """

                    iframe = branca.element.IFrame(html=html, width=350, height=150)
                    popup_text = folium.Popup(iframe,parse_html=True)
                    icon = folium.Icon(icon="pagelines",color="pink",prefix="fa")
                    folium.Marker(location=[row['위도'], row['경도']],
                                  popup=popup_text, tooltip=row['이름'], icon=icon).add_to(m)

                start = (longit,lati)

                goal = (short_load.iloc[0]['경도'],short_load.iloc[0]['위도'])

                short = results(get_optimal_route(start,goal))
                folium.PolyLine(locations=short, color='#3098FE').add_to(m)


                st_folium(m, width=1000)
                st.dataframe(display_dff)

with tab2:
    st.markdown("## 양봉장 밀원 분포지도")

    display_df = pd.read_csv('/content/drive/MyDrive/빅프csv/양봉qhd.csv',encoding="cp949")
    display_df2 = pd.read_csv('/content/drive/MyDrive/빅프csv/꽃지도.csv',encoding="cp949")

    distance2 = []

    for idx1, row1 in display_df.iterrows():
        flower = '야생화,'
        for idx2, row2 in display_df2.iterrows():
            rounded_distance = round(haversine((row2['위도'], row2['경도']), (row1['위도'], row1['경도']), unit='km'), 2)

            if rounded_distance <= 2:
                flower += row2['꽃'] + ','

        flowers = [i.strip() for i in flower.rstrip(',').split(',')]
        # 중복 제거
        unique_flowers = list(set(flowers))
        unique_flowers_join = ', '.join(unique_flowers)
        distance2.append(unique_flowers_join)

    display_df['인근 꽃 정보'] = distance2

    display_dff = display_df.drop(['위도','경도'],axis=1)

    #### 사고위치
    with st.expander("꽃 지도", expanded=True):
        lati, longit = geocoding(address)
        m = folium.Map(location=[lati,longit], zoom_start=12)
        # 양봉지도
        for idx, row in display_df[:].iterrows():
            html = """<!DOCTYPE html>
                <html>
                    <table style="height: 126px; width: 330px;"> <tbody> <tr>
                        <td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">양봉지명</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['이름'])+"""</tr>
                        <tr><td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">주소</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['주소'])+"""</tr>
                        <tr><td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">인근 꽃 정보</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['인근 꽃 정보'])+"""</tr>
                        <tr><td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">연락처</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['연락처'])+"""</tr>
                    </tbody> </table> </html> """

            iframe = branca.element.IFrame(html=html, width=360, height=200)
            popup_text = folium.Popup(iframe,parse_html=True)
            icon = folium.Icon(icon="forumbee",color="orange",prefix="fa")
            folium.Marker(location=[row['위도'], row['경도']],
                            popup=popup_text, tooltip=row['이름'], icon=icon).add_to(m)

        # 꽃지도
        for idx, row in display_df2[:].iterrows():
            html = """<!DOCTYPE html>
                <html>
                    <table style="height: 126px; width: 330px;"> <tbody> <tr>
                        <td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">이름</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['이름'])+"""</tr>
                        <tr><td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">주소</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['주소'])+"""</tr>
                        <tr><td style="background-color: #F2952F;">
                        <div style="color: #ffffff;text-align:center;">꽃</div></td>
                        <td style="width: 230px;background-color: #FFBF00;text-align: center; color: white;">{}</td>""".format(row['꽃'])+"""</tr>
                    </tbody> </table> </html> """

            iframe = branca.element.IFrame(html=html, width=350, height=150)
            popup_text = folium.Popup(iframe,parse_html=True)
            icon = folium.Icon(icon="pagelines",color="pink",prefix="fa")
            folium.Marker(location=[row['위도'], row['경도']],
                            popup=popup_text, tooltip=row['이름'], icon=icon).add_to(m)

        
        st_folium(m, width=1000)
        st.dataframe(display_dff)
