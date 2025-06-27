import aiohttp
import asyncio
import xmltodict
import retrying
import pandas as pd
from datetime import datetime, timedelta, date
from tqdm import tqdm
import requests
import streamlit as st

url="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
headers = {'content-type': 'text/xml;charset=UTF-8','SOAPAction':"xxxxxxxxxxxxxxxxxxxxxxxx",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
           "Accept-Encoding":"gzip,deflate","Connection": "keep-alive","Cache-Control": "no-cache"}

#@retrying.retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
async def GetRates(session,jpcode,checkin,checkout,x,nationality,rates_df):

    body=f"""<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
    <OTA_HotelAvailService xmlns="http://www.opentravel.org/OTA/2003/05">
    <OTA_HotelAvailRQ PrimaryLangID="en">
        <POS>
            <Source AgentDutyCode="xxxxxxxxxxxxxxxxxxxxxx">
                <RequestorID Type="1" MessagePassword="xxxxxxxxxxxxxxxxxxx"/>
            </Source>
        </POS>
        <AvailRequestSegments>
            <AvailRequestSegment>
                <StayDateRange Start="{checkin}" End="{checkout}"/>
                <RoomStayCandidates>
                    {x}
                </RoomStayCandidates>
                <HotelSearchCriteria>
                    <Criterion><HotelRef HotelCode="{jpcode}" />
                        <TPA_Extensions>
                            <ShowOnlyAvailable>1</ShowOnlyAvailable>
                            <ShowInternalRoomInfo>1</ShowInternalRoomInfo>
                            <ShowInternalProvInfo>1</ShowInternalProvInfo>
                            <ShowCatalogueData>1</ShowCatalogueData>
                            <PackageContracts>Package</PackageContracts>
                            <ShowDailyAvailabilityBreakdown>0</ShowDailyAvailabilityBreakdown>
                            <ShowBasicInfo>1</ShowBasicInfo>
                            <PaxCountry>{nationality}</PaxCountry>
                            <SearchTimeOut>5000</SearchTimeOut>
                        </TPA_Extensions>
                    </Criterion>
                </HotelSearchCriteria>
            </AvailRequestSegment>
        </AvailRequestSegments>
    </OTA_HotelAvailRQ>
    </OTA_HotelAvailService>
    </soap:Body>
    </soap:Envelope>"""

    async with session.post(url, data=body, headers=headers) as response:
        responseDict = xmltodict.parse(await response.text())
    
    try:
        data = responseDict['soap:Envelope']['soap:Body']['OTA_HotelAvailServiceResponse']['OTA_HotelAvailRS']['RoomStays']['RoomStay']['RoomRates']['RoomRate']
        hotelname = responseDict['soap:Envelope']['soap:Body']['OTA_HotelAvailServiceResponse']['OTA_HotelAvailRS']['RoomStays']['RoomStay']['BasicPropertyInfo']['@HotelName']
        
        if isinstance(data,list):
            #st.write(data)
                for i in data:
                    try:
                        boardType = i['@RatePlanCategory']
                        rateplan = i['@RatePlanCode']
                        try:
                            RF = i['TPA_Extensions']['NonRefundable']['#text']
                            if RF == "1":
                                RF = 'NRF'
                            else:
                                RF = 'RF'
                        except:
                            RF = "--"
                        rate=0
                        if isinstance(i['Rates']['Rate'],list):
                            for z in range(len(i['Rates']['Rate'])):
                                no_unites = i['Rates']['Rate'][z]['@NumberOfUnits']
                                roomType = i['Rates']['Rate'][z]['RateDescription']['Text']
                                rate += round(float(i['Rates']['Rate'][z]['Total']['@AmountAfterTax'])*int(no_unites),2)
                            row = [hotelname,boardType,roomType,rate,RF,rateplan]
                            rates_df.loc[len(rates_df)]=row
                        else:
                            no_unites = i['Rates']['Rate']['@NumberOfUnits']
                            roomType = i['Rates']['Rate']['RateDescription']['Text']
                            rate = round(float(i['Rates']['Rate']['Total']['@AmountAfterTax'])*int(no_unites),2)
                            row = [jpcode,hotelname,boardType,roomType,rate,RF,rateplan]
                            rates_df.loc[len(rates_df)]=row
                    except:
                        pass

        else:
            try:
                boardType = data['@RatePlanCategory']
                rateplan = data['@RatePlanCode']
                roomType = data['Rates']['Rate']['RateDescription']['Text']
                rate = round(data['Rates']['Rate']['Total']['@AmountAfterTax'],2)
                try:
                    RF = data['TPA_Extensions']['NonRefundable']['#text']
                    if RF == "1":
                        RF = 'NRF'
                    else:
                        RF = 'RF'
                except:
                    RF = "--"
                row = [jpcode,hotelname,boardType,roomType,rate,RF,rateplan]
                
                rates_df.loc[len(rates_df)]=row
            except:
                pass
        #return rates_df
    except Exception as e:
        # try:
        #     error = response['soap:Envelope']['soap:Body']['OTA_HotelAvailServiceResponse']['OTA_HotelAvailRS']['Errors']['ErrorType']['@ShortText']
        # except:
        pass
    #pbar.update(1)

async def main(jpcodes,checkin,checkout,x,nationality):
    rates_df = pd.DataFrame(columns=['JPCode','HotelName','BoardType','RoomType','Rate','Refundable/Not','rateplan'])
    async with aiohttp.ClientSession() as session:
        tasks = []
        for jp in jpcodes:
            tasks.append(asyncio.ensure_future(GetRates(session,jp,checkin,checkout,x,nationality,rates_df)))
        await asyncio.gather(*tasks)
        return(rates_df)
             

#asyncio.run(main())
