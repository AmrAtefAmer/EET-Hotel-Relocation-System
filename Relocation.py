from HotelsAvailabiltyApi import *
from HotelsAvailabiltyApi import main
import streamlit as st
st.set_page_config(layout='wide',page_icon=":hotel:")
#from datetime import datetime, timedelta, date
#import numpy as np
#from pandas import json_normalize
#import time
#from bs4 import BeautifulSoup
import warnings
#from streamlit_modal import Modal
import folium
from streamlit.components.v1 import html
from geopy.distance import geodesic
import json
warnings.filterwarnings("ignore")
pd.set_option('styler.render.max_elements', 714582)
pd.set_option('display.max_columns', None)

st.title("EET Global Relocaion System!")

url = r"C:\Users\Administrator\Desktop\Relocation system\EET_External_Temp.xlsx"
#Read All EET Hotels Data
@st.cache_data
def read_EET_data(url):
    # Fetch data from URL here, and then clean it up.
    hotels_df = pd.read_excel(url)
    hotels_df['Latitude'] = hotels_df['Latitude'].apply(lambda x : x.strip())
    hotels_df['Longitude'] = hotels_df['Longitude'].apply(lambda x : x.strip())
    return hotels_df

hotels_df = read_EET_data(url)


df = pd.DataFrame(columns=['BookingCode','Description','Supplier Name','First Name','Last Name', 'BookingDate', 'Status', 'Remarks', 'BeginTravelDate',
                           'EndTravelDate', 'Channel', 'Agency', 'Product Group','SupplierCodExport','CancellationDate','NationalityId','Nationality',
                           'SellingPrice','No.Rooms','RoomData','JPCode','BoardType','Ages','Country','RoomNames'])
def GetBookingData(code):
    url = "https://www.eetglobal.com/wsExportacion/wsBookings.asmx"
    headers = {
        'content-type': 'text/xml',
        'SOAPAction': "http://juniper.es/getBookings",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
        "Accept-Encoding": "*",
        "Connection": "keep-alive"
    }
    body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <getBookings xmlns="http://juniper.es/">
              <user>internet03</user>
              <password>P@$$w0rd09</password>
              <BookingCode>{code}</BookingCode>
            </getBookings>
          </soap:Body>
        </soap:Envelope>"""
    try:
        response = requests.post(url, data=body, headers=headers)
        responseDict = xmltodict.parse(response.text)
        AllBookings = responseDict['soap:Envelope']['soap:Body']['getBookingsResponse']['getBookingsResult']['wsResult']['Bookings']['Booking']
        if isinstance(AllBookings['Lines']['Line'], list):
            for j in range(len(AllBookings['Lines']['Line'])):
                try:
                    ages = []
                    roomnames = []
                    if isinstance(AllBookings['Lines']['Line'][j]['Paxes']['Pax'], list):
                        for lp in AllBookings['Lines']['Line'][j]['Paxes']['Pax']:
                            ages.append(lp['Age'])
                    else:
                        ages.append(AllBookings['Lines']['Line'][j]['Paxes']['Pax']['Age'])
                        
                    if isinstance(AllBookings['Lines']['Line'][j]['roomlist']['room'], list):
                        try:
                            JPCode = AllBookings['Lines']['Line'][j]['roomlist']['room'][0]['JPCode']
                        except:
                            JPCode = "Not Available"
                        boardType = AllBookings['Lines']['Line'][j]['roomlist']['room'][0]['boardtype']['#text']
                        rooms = len(AllBookings['Lines']['Line'][j]['roomlist']['room'])
                        room_data = {}

                        for r in range(1,rooms+1):
                            roomnames.append(AllBookings['Lines']['Line'][j]['roomlist']['room'][r-1]['typeroomname'])
                            adult=0
                            child=0
                            baby=0
                            if isinstance(AllBookings['Lines']['Line'][j]['roomlist']['room'][r-1]['paxes']['pax'], list):
                                for p in range(len(AllBookings['Lines']['Line'][j]['roomlist']['room'][r-1]['paxes']['pax'])):
                                    pax_type = AllBookings['Lines']['Line'][j]['roomlist']['room'][r-1]['paxes']['pax'][p]['typepax']
                                    if pax_type == 'Adult':
                                        adult+=1
                                    if pax_type == 'Child':
                                        child+=1
                                    if pax_type == 'Baby':
                                        child+=1
                            else:
                                pax_type = AllBookings['Lines']['Line'][j]['roomlist']['room'][r-1]['paxes']['pax']['typepax']
                                if pax_type == 'Adult':
                                    adult+=1
                                if pax_type == 'Child':
                                    child+=1
                                if pax_type == 'Baby':
                                    child+=1
                            
                            room_data[r] = [adult, child]        
                    
                    else:
                        rooms = 1
                        roomnames.append(AllBookings['Lines']['Line'][j]['roomlist']['room']['typeroomname'])
                        try:
                            JPCode = AllBookings['Lines']['Line'][j]['roomlist']['room']['JPCode']
                        except:
                            JPCode = "Not Available"
                        boardType = AllBookings['Lines']['Line'][j]['roomlist']['room']['boardtype']['#text']
                        room_data = {}
                        adult=0
                        child=0
                        baby=0
                        if isinstance(AllBookings['Lines']['Line'][j]['roomlist']['room']['paxes']['pax'], list):
                            for p in range(len(AllBookings['Lines']['Line'][j]['roomlist']['room']['paxes']['pax'])):
                                pax_type = AllBookings['Lines']['Line'][j]['roomlist']['room']['paxes']['pax'][p]['typepax']
                                if pax_type == 'Adult':
                                    adult+=1
                                if pax_type == 'Child':
                                    child+=1
                                if pax_type == 'Baby':
                                    child+=1
                        else:
                            pax_type = AllBookings['Lines']['Line'][j]['roomlist']['room']['paxes']['pax']['typepax']
                            if pax_type == 'Adult':
                                adult+=1
                            if pax_type == 'Child':
                                child+=1
                            if pax_type == 'Baby':
                                child+=1
                            
                        room_data[1] = [adult, child]
                except:
                    rooms = None
                    room_data = {}
                    roomnames = []
                room_data = json.dumps(room_data)
                row = [
                    AllBookings['@BookingCode'],
                    AllBookings['Lines']['Line'][j]['ServiceName'],
                    AllBookings['Lines']['Line'][j]['Supplier']['SupplierName'],
                    AllBookings['Holder']['NameHolder'],
                    AllBookings['Holder']['LastName'],
                    AllBookings['@BookingDate'],
                    AllBookings['@Status'],
                    AllBookings['Remarks'],
                    AllBookings['Lines']['Line'][j]['BeginTravelDate'][:AllBookings['Lines']['Line'][j]['BeginTravelDate'].index('T')],
                    AllBookings['Lines']['Line'][j]['EndTravelDate'][:AllBookings['Lines']['Line'][j]['EndTravelDate'].index('T')],
                    AllBookings['@Channel'],
                    AllBookings['Customer']['Name'],
                    AllBookings['Lines']['Line'][j]['ProductGroupName'],
                    AllBookings['Lines']['Line'][j]['Supplier']['SupplierCodExport'],
                    AllBookings['Lines']['Line'][j]['@LineCancelledDate'],
                    AllBookings['Holder']['Nacionalidad']['@ISO2'],
                    AllBookings['Holder']['Nacionalidad']['#text'],
                    AllBookings['Lines']['Line'][j]['SellingPrice'],
                    rooms,
                    room_data,
                    JPCode,
                    boardType,
                    ages,
                    AllBookings['Lines']['Line'][j]['Zone']['country'],
                    roomnames
                ]
                df.loc[len(df)] = row
        else:
            try:
                ages = []
                roomnames = []
                if isinstance(AllBookings['Lines']['Line']['Paxes']['Pax'], list):  
                    for lp in (AllBookings['Lines']['Line']['Paxes']['Pax']):
                        ages.append(lp['Age'])
                else:
                    ages.append(AllBookings['Lines']['Line']['Paxes']['Pax']['Age'])
                   
                if isinstance(AllBookings['Lines']['Line']['roomlist']['room'], list):
                    try:
                        JPCode = AllBookings['Lines']['Line']['roomlist']['room'][0]['JPCode']
                    except:
                        JPCode = "Not Available"
                    boardType = AllBookings['Lines']['Line']['roomlist']['room'][0]['boardtype']['#text']
                    rooms = len(AllBookings['Lines']['Line']['roomlist']['room'])
                    room_data = {}
                    for r in range(1,rooms+1):
                        roomnames.append(AllBookings['Lines']['Line']['roomlist']['room'][r-1]['typeroomname'])
                        adult=0
                        child=0
                        baby=0
                        if isinstance(AllBookings['Lines']['Line']['roomlist']['room'][r-1]['paxes']['pax'], list):
                            for p in range(len(AllBookings['Lines']['Line']['roomlist']['room'][r-1]['paxes']['pax'])):
                                pax_type = AllBookings['Lines']['Line']['roomlist']['room'][r-1]['paxes']['pax'][p]['typepax']
                                if pax_type == 'Adult':
                                    adult+=1
                                if pax_type == 'Child':
                                    child+=1
                                if pax_type == 'Baby':
                                    child+=1
                        else:
                            pax_type = AllBookings['Lines']['Line']['roomlist']['room'][r-1]['paxes']['pax']['typepax']
                            if pax_type == 'Adult':
                                adult+=1
                            if pax_type == 'Child':
                                child+=1
                            if pax_type == 'Baby':
                                child+=1

                        room_data[r] = [adult, child]        
                else:
                    rooms = 1
                    roomnames.append(AllBookings['Lines']['Line']['roomlist']['room']['typeroomname'])
                    try:
                        JPCode = AllBookings['Lines']['Line']['roomlist']['room']['JPCode']
                    except:
                        JPCode = "Not Available"
                    boardType = AllBookings['Lines']['Line']['roomlist']['room']['boardtype']['#text']
                    room_data = {}
                    adult=0
                    child=0
                    baby=0
                    if isinstance(AllBookings['Lines']['Line']['roomlist']['room']['paxes']['pax'], list):
                        for p in range(len(AllBookings['Lines']['Line']['roomlist']['room']['paxes']['pax'])):
                            pax_type = AllBookings['Lines']['Line']['roomlist']['room']['paxes']['pax'][p]['typepax']
                            if pax_type == 'Adult':
                                adult+=1
                            if pax_type == 'Child':
                                child+=1
                            if pax_type == 'Baby':
                                child+=1
                    else:
                        pax_type = AllBookings['Lines']['Line']['roomlist']['room']['paxes']['pax']['typepax']
                        if pax_type == 'Adult':
                            adult+=1
                        if pax_type == 'Child':
                            child+=1
                        if pax_type == 'Baby':
                            child+=1
                        
                    room_data[1] = [adult, child]
            except:
                rooms = None
                room_data = {}
                roomnames=[]
            room_data = json.dumps(room_data)
            row = [
                AllBookings['@BookingCode'],
                AllBookings['Lines']['Line']['ServiceName'],
                AllBookings['Lines']['Line']['Supplier']['SupplierName'],
                AllBookings['Holder']['NameHolder'],
                AllBookings['Holder']['LastName'],
                AllBookings['@BookingDate'],
                AllBookings['@Status'],
                AllBookings['Remarks'],
                AllBookings['Lines']['Line']['BeginTravelDate'][:AllBookings['Lines']['Line']['BeginTravelDate'].index('T')],
                AllBookings['Lines']['Line']['EndTravelDate'][:AllBookings['Lines']['Line']['EndTravelDate'].index('T')],
                AllBookings['@Channel'],
                AllBookings['Customer']['Name'],
                AllBookings['Lines']['Line']['ProductGroupName'],
                AllBookings['Lines']['Line']['Supplier']['SupplierCodExport'],
                AllBookings['Lines']['Line']['@LineCancelledDate'],
                AllBookings['Holder']['Nacionalidad']['@ISO2'],
                AllBookings['Holder']['Nacionalidad']['#text'],
                AllBookings['Lines']['Line']['SellingPrice'],
                rooms,
                room_data,
                JPCode,
                boardType,
                ages,
                AllBookings['Lines']['Line']['Zone']['country'],
                roomnames
            ]
            df.loc[len(df)] = row
        return df
    except Exception as e:
        return e


booking_input = st.text_input("Enter Booking Code", placeholder="Enter Booking Code!", label_visibility='collapsed')

df = GetBookingData(booking_input)

def mapBoard(x):
    if 'breakfast' in x.lower() or 'alojamiento y desayuno' in x.lower():
        return 'Breakfast'
    elif 'inclusive' in x.lower():
        return 'Inclusive'
    elif 'room only' in x.lower():
        return 'Room Only'
    elif 'half' in x.lower():
        return 'Half Board'
    elif 'full' in x.lower():
        return 'Full Board'
    elif 'lunch' in x.lower():
        return 'Lunch'
    elif 'dinner' in x.lower():
        return 'Dinner'
    elif "sólo alojamiento" in x.lower():
        return 'Room Only'
    elif "room and board" in x.lower():
        return 'Room and Board'
    
if type(df) == pd.core.frame.DataFrame:
    show_df = df[['BookingCode','Description','First Name','Last Name', 'BookingDate', 'Status', 'Remarks', 'BeginTravelDate',
                 'EndTravelDate', 'Agency', 'Product Group','Nationality','SellingPrice','No.Rooms','RoomData','JPCode','BoardType','Ages','Country','RoomNames']]
    st.dataframe(show_df)
    col3,col4,col5,col6,boardcol,col7 = st.columns(6)
    with col3:
        jpcode_input = st.text_input("JPCode", value = df['JPCode'].values[0], placeholder="JPCode", label_visibility='visible')
    with col4:
        nationality_input = st.text_input("Nationality", value = df['Nationality'].values[0], placeholder="Nationality", label_visibility='visible',disabled=True)
    with col5:
        checkin_input = st.text_input("Check-in", value = df['BeginTravelDate'].values[0], placeholder="Check-in Date", label_visibility='visible',disabled=True)
    with col6:
        checkout_input = st.text_input("Check-out", value = df['EndTravelDate'].values[0], placeholder="Check-out Date", label_visibility='visible',disabled=True)
    with boardcol:
        boardType_input = st.text_input("Board Type", value = df['BoardType'].values[0], placeholder="Board Type", label_visibility='visible',disabled=True)
    with col7:
        rooms_input = st.text_input("Rooms No.", value = df['No.Rooms'].values[0], placeholder="Number Rooms", label_visibility='visible',disabled=True)
    total_paxes = 0
    all_ages = list(df['Ages'].values)[0]
    x=""
    for r in range(1,df['No.Rooms'].values[0]+1):
        child_no = json.loads((df['RoomData'].values[0]))[str(r)][1]
        adults_no = json.loads((df['RoomData'].values[0]))[str(r)][0]
        room_paxes = child_no+adults_no
        room_ages = all_ages[total_paxes:room_paxes+total_paxes]
        child_ages = room_ages[adults_no:]
        total_paxes+=room_paxes
        if child_no == 0:
            adults_input = st.text_input(f"Adults_{r}", value = adults_no, placeholder="Adults", label_visibility='visible',disabled=True)
            x+=f"""<RoomStayCandidate Quantity="1">
                    <GuestCounts><GuestCount Count="{adults_no}"/></GuestCounts>
                   </RoomStayCandidate>"""
        elif child_no != 0:
            ch = ""
            total_fields = 2+(child_no)
            columns = st.columns(total_fields)
            with columns[0]:
                adults_input = st.text_input(f"Adults_{r}", value = adults_no, placeholder="Adults", label_visibility='visible',disabled=True)
            with columns[1]:
                childs_input = st.text_input(f"Childs_{r}", value = child_no, placeholder="Adults", label_visibility='visible',disabled=True)
            for field in range(child_no):
                with columns[total_fields-child_no+field]:
                    Ages = st.text_input(f"Age_{r}_{field}", value = child_ages[field], placeholder="Childs", label_visibility='visible',disabled=True)
                    ch += ""f'<GuestCount Age="{child_ages[field]}" Count="1" />'""
            x += f"""<RoomStayCandidate Quantity="1">
                <GuestCounts>
                <GuestCount Count="{adults_no}"/>
                {ch}
                </GuestCounts>
            </RoomStayCandidate>""" 
    #st.markdown(x)

    JPCode = jpcode_input #JPCode from input field
    
    hotel_col, search_col = st.columns(2)
    with hotel_col:
        need_hotels = st.text_input("Nearest Hotels No.", value = 10, placeholder="Nearest Hotels Number!", label_visibility='collapsed')
    with search_col:
        search_button_clicked = st.button("Search", use_container_width=True, type='primary')
    
    if search_button_clicked:
        st.cache_resource.clear()
        if JPCode == "Not Available":
            st.error('JPCode not available', icon="⚠️")
        elif need_hotels=='':
            st.error('Please enter the number of nearest hotels', icon="⚠️")
        else:
            need_hotels = int(need_hotels)+1
            lat = hotels_df[hotels_df['JPCode']==JPCode]['Latitude'].values[0]
            long = hotels_df[hotels_df['JPCode']==JPCode]['Longitude'].values[0]
            main_hotel = hotels_df[hotels_df['JPCode']==JPCode]['Accommodation Name'].values[0] #df['Description'].values[0] #
            main_country = hotels_df[hotels_df['JPCode']==JPCode]['Zone level 1'].values[0] #df['Country'].values[0] #
            #st.markdown(f"JPCode Juniper Name -> {main_hotel}, and Country ->  {main_country}")
            my_bar = st.progress(0, text="Getting Nearest Hotels...")
            progress = 0
            update = 0
            hotels_df2 = hotels_df[hotels_df['Zone level 1']==main_country]
            for row, v in hotels_df2.iterrows():
                hotels_df2.at[row,'Distance'] = round(geodesic((lat, long), (hotels_df2.at[row,'Latitude'], hotels_df2.at[row,'Longitude'])).meters,1)
                progress+=1
                
                update = progress / len(hotels_df2)
                
                my_bar.progress(update, text="Getting Nearest Hotels...")
                
            hotels_df2 = hotels_df2.sort_values(by=['Distance'])
            hotels_df2 = hotels_df2[['JPCode', 'Accommodation Name','Distance', 'Category', 'Zone Name', 'Address','Latitude', 'Longitude','Zone level 1','Zone level 2','Zone level 3']]
            nearest_hotels = hotels_df2.head(need_hotels).reset_index().iloc[1:]
            m = folium.Map(location=[lat, long], width=1200, height=500, zoom_start=14)
            folium.Marker([lat, long],popup=main_hotel,tooltip=main_hotel,icon=folium.Icon(color='orange', icon='info-sign')).add_to(m)
            for i, v in nearest_hotels.iterrows():
                folium.Marker([nearest_hotels.at[i,'Latitude'], nearest_hotels.at[i,'Longitude']],
                              popup=nearest_hotels.at[i,'Accommodation Name'],
                              tooltip=f"{nearest_hotels.at[i,'Accommodation Name']} --> {nearest_hotels.at[i,'Distance']:.2f} meteres").add_to(m)
            with st.expander("Nearest Hotels"):
                nearest_hotels = nearest_hotels.drop('index', axis=1)
                st.dataframe(nearest_hotels,use_container_width=True,hide_index=True)
                map_html = m._repr_html_()  # Get the HTML representation of the Folium map
                html(map_html, height=500)

            if checkin_input >= datetime.now().strftime(f"%Y-%m-%d"):
                jps = nearest_hotels['JPCode'].to_list()
                result = asyncio.run(main(jps, checkin_input, checkout_input, x, df['NationalityId'].values[0]))
                sell_rate = float(df['SellingPrice'].values[0])
                min_rate = (sell_rate-(sell_rate*0.2))
                max_rate = (sell_rate+(sell_rate*0.2))
                mapped_board = mapBoard(df['BoardType'].values[0])
                result['Mapped_Board']=result['BoardType'].apply(lambda x : mapBoard(x))
                result2 = result[(result['Rate']<=max_rate) & (result['Mapped_Board']==mapped_board)]
                result2 =result2.drop_duplicates(subset=['JPCode','RoomType'])
                with st.expander("Nearest Hotels With Availability"):
                    st.markdown(f"Total Hotels with Availability: {result['JPCode'].nunique()} ")
                    st.dataframe(result[['JPCode','HotelName','BoardType','RoomType','Rate','Refundable/Not']],use_container_width=True,hide_index=True)
                with st.expander("Nearest Hotels With Availability After filteration"):
                    st.markdown(f"Total Hotels with Availability After Filteration: {result2['JPCode'].nunique()} ")
                    st.dataframe(result2[['JPCode','HotelName','BoardType','RoomType','Rate','Refundable/Not']],use_container_width=True,hide_index=True)
                st.link_button("Go to Call Center", "https://www.eetglobal.com/intranet/callcenter/")    
            else:
                st.error('Check-in date was in the past', icon="⚠️")
                    #map_html = m._repr_html_()  # Get the HTML representation of the Folium map
                    #html(map_html, height=500)
                    
                
            

elif booking_input == '':
    pass
else:
    st.error('Please make sure you entered a valid booking code and it not a generic booking', icon="⚠️")

st.write("Developed By: **Eng. Amr Atef** ⌨️")






















