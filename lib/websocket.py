""" Handles Websocket messages received by the Raspberry Pi Python console for
eather Flow Smart Home Weather Stations. Copyright (C) 2018-2020  Peter Davis

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

# Import required library modules
from lib import derivedVariables   as derive
from lib import observationFormat  as observation
from lib import requestAPI

# Define global variables
NaN = float('NaN')

def Tempest(Msg,Obs,Config):

    """ Handles Websocket messages received from TEMPEST module

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Replace missing observations from latest SKY Websocket JSON with NaN
    Ob = [x if x != None else NaN for x in Msg['obs'][0]]

    # Extract TEMPEST device ID
    Device = Config['Station']['TempestID']

    # Extract required observations from latest TEMPEST Websocket JSON
    Time      = [Ob[0],'s']
    WindSpd   = [Ob[2],'mps']
    WindGust  = [Ob[3],'mps']
    WindDir   = [Ob[4],'degrees']
    Pres      = [Ob[6],'mb']
    Temp      = [Ob[7],'c']
    Humidity  = [Ob[8],' %']
    UV        = [Ob[10],'index']
    Radiation = [Ob[11],' W m[sup]-2[/sup]']
    Rain      = [Ob[12],'mm']
    Strikes   = [Ob[15],'count']
    Battery   = [Ob[16],' v']

    # Extract lightning strike data from the latest AIR Websocket JSON "Summary"
    # object
    StrikeTime = [Msg['summary']['strike_last_epoch'] if 'strike_last_epoch' in Msg['summary'] else NaN,'s']
    StrikeDist = [Msg['summary']['strike_last_dist']  if 'strike_last_dist'  in Msg['summary'] else NaN,'km']
    Strikes3hr = [Msg['summary']['strike_count_3h']   if 'strike_count_3h'   in Msg['summary'] else NaN,'count']

    # Store latest TEMPEST Websocket message
    Obs['TempestMsg'] = Msg

    # Extract required derived observations
    minPres     = Obs['MinPres']
    maxPres     = Obs['MaxPres']
    minTemp     = Obs['outTempMin']
    maxTemp     = Obs['outTempMax']
    StrikeCount = {'Today': Obs['StrikesToday'],
                   'Month': Obs['StrikesMonth'],
                   'Year':  Obs['StrikesYear']}
    rainAccum   = {'Today':     Obs['TodayRain'],
                   'Yesterday': Obs['YesterdayRain'],
                   'Month':     Obs['MonthRain'],
                   'Year':      Obs['YearRain']}
    avgWind     = Obs['AvgWind']
    maxGust     = Obs['MaxGust']

    # Request TEMPEST data from the previous three hours
    Data3h = requestAPI.weatherflow.Last3h(Device,Time[0],Config)

    # Calculate derived variables from TEMPEST observations
    DewPoint         = derive.DewPoint(Temp,Humidity)
    SLP              = derive.SLP(Pres,Config)
    PresTrend        = derive.SLPTrend(Pres,Time,Data3h,Config)
    FeelsLike        = derive.FeelsLike(Temp,Humidity,WindSpd,Config)
    MaxTemp, MinTemp = derive.TempMaxMin(Time,Temp,maxTemp,minTemp,Device,Config)
    MaxPres, MinPres = derive.SLPMaxMin(Time,Pres,maxPres,minPres,Device,Config)
    StrikeCount      = derive.StrikeCount(Strikes,StrikeCount,Device,Config)
    StrikeFreq       = derive.StrikeFrequency(Time,Data3h,Config)
    StrikeDeltaT     = derive.StrikeDeltaT(StrikeTime)
    FeelsLike        = derive.FeelsLike(Temp,Humidity,WindSpd,Config)
    RainRate         = derive.RainRate(Rain)
    rainAccum        = derive.RainAccumulation(Rain,rainAccum,Device,Config)
    AvgWind          = derive.MeanWindSpeed(WindSpd,avgWind,Device,Config)
    MaxGust          = derive.MaxWindGust(WindGust,maxGust,Device,Config)
    WindSpd          = derive.BeaufortScale(WindSpd)
    WindDir          = derive.CardinalWindDirection(WindDir,WindSpd)
    UVIndex          = derive.UVIndex(UV)

    # Convert observation units as required
    Temp          = observation.Units(Temp,Config['Units']['Temp'])
    MaxTemp       = observation.Units(MaxTemp,Config['Units']['Temp'])
    MinTemp       = observation.Units(MinTemp,Config['Units']['Temp'])
    DewPoint      = observation.Units(DewPoint,Config['Units']['Temp'])
    FeelsLike     = observation.Units(FeelsLike,Config['Units']['Temp'])
    SLP           = observation.Units(SLP,Config['Units']['Pressure'])
    MaxPres       = observation.Units(MaxPres,Config['Units']['Pressure'])
    MinPres       = observation.Units(MinPres,Config['Units']['Pressure'])
    PresTrend     = observation.Units(PresTrend,Config['Units']['Pressure'])
    StrikeDist    = observation.Units(StrikeDist,Config['Units']['Distance'])
    RainRate      = observation.Units(RainRate,Config['Units']['Precip'])
    TodayRain     = observation.Units(rainAccum['Today'],Config['Units']['Precip'])
    YesterdayRain = observation.Units(rainAccum['Yesterday'],Config['Units']['Precip'])
    MonthRain     = observation.Units(rainAccum['Month'],Config['Units']['Precip'])
    YearRain      = observation.Units(rainAccum['Year'],Config['Units']['Precip'])
    WindSpd       = observation.Units(WindSpd,Config['Units']['Wind'])
    WindDir       = observation.Units(WindDir,Config['Units']['Direction'])
    WindGust      = observation.Units(WindGust,Config['Units']['Wind'])
    AvgWind       = observation.Units(AvgWind,Config['Units']['Wind'])
    MaxGust       = observation.Units(MaxGust,Config['Units']['Wind'])
    FeelsLike     = observation.Units(FeelsLike,Config['Units']['Temp'])

    # Define Kivy label binds
    Obs['outTemp']       = observation.Format(Temp,'Temp')
    Obs['outTempMax']    = observation.Format(MaxTemp,'Temp')
    Obs['outTempMin']    = observation.Format(MinTemp,'Temp')
    Obs['DewPoint']      = observation.Format(DewPoint,'Temp')
    Obs['FeelsLike']     = observation.Format(FeelsLike,'Temp')
    Obs['Pres']          = observation.Format(SLP,'Pressure')
    Obs['MaxPres']       = observation.Format(MaxPres,'Pressure')
    Obs['MinPres']       = observation.Format(MinPres,'Pressure')
    Obs['PresTrend']     = observation.Format(PresTrend,'Pressure')
    Obs['StrikeDeltaT']  = observation.Format(StrikeDeltaT,'TimeDelta')
    Obs['StrikeDist']    = observation.Format(StrikeDist,'StrikeDistance')
    Obs['StrikeFreq']    = observation.Format(StrikeFreq,'StrikeFrequency')
    Obs['Strikes3hr']    = observation.Format(Strikes3hr,'StrikeCount')
    Obs['StrikesToday']  = observation.Format(StrikeCount['Today'],'StrikeCount')
    Obs['StrikesMonth']  = observation.Format(StrikeCount['Month'],'StrikeCount')
    Obs['StrikesYear']   = observation.Format(StrikeCount['Year'],'StrikeCount')
    Obs['Humidity']      = observation.Format(Humidity,'Humidity')
    Obs['Battery']       = observation.Format(Battery,'Battery')
    Obs['FeelsLike']     = observation.Format(FeelsLike,'Temp')
    Obs['RainRate']      = observation.Format(RainRate,'Precip')
    Obs['TodayRain']     = observation.Format(TodayRain,'Precip')
    Obs['YesterdayRain'] = observation.Format(YesterdayRain,'Precip')
    Obs['MonthRain']     = observation.Format(MonthRain,'Precip')
    Obs['YearRain']      = observation.Format(YearRain,'Precip')
    Obs['WindSpd']       = observation.Format(WindSpd,'Wind')
    Obs['WindGust']      = observation.Format(WindGust,'Wind')
    Obs['AvgWind']       = observation.Format(AvgWind,'Wind')
    Obs['MaxGust']       = observation.Format(MaxGust,'Wind')
    Obs['WindDir']       = observation.Format(WindDir,'Direction')
    Obs['Radiation']     = observation.Format(Radiation,'Radiation')
    Obs['Battery']       = observation.Format(Battery,'Battery')
    Obs['UVIndex']       = observation.Format(UVIndex,'UV')

    # Return Station observations
    return Obs

def Sky(Msg,Obs,Config):

    """ Handles Websocket messages received from SKY module

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Replace missing observations from latest SKY Websocket JSON with NaN
    Ob = [x if x != None else NaN for x in Msg['obs'][0]]

    # Extract SKY device ID
    Device = Config['Station']['SkyID']

    # Extract required observations from latest SKY Websocket JSON
    Time      = [Ob[0],'s']
    UV        = [Ob[2],'index']
    Rain      = [Ob[3],'mm']
    WindSpd   = [Ob[5],'mps']
    WindGust  = [Ob[6],'mps']
    WindDir   = [Ob[7],'degrees']
    Battery   = [Ob[8],'v']
    Radiation = [Ob[10],' W m[sup]-2[/sup]']

    # Store latest SKY Websocket message
    Obs['SkyMsg'] = Msg

    # Extract required observations from latest AIR Websocket observations
    if 'outAirMsg' in Obs:
        Ob = [x if x != None else NaN for x in Obs['outAirMsg']['obs'][0]]
        Temp = [Ob[2],'c']
        Humidity = [Ob[3],'%']
    else:
        Temp = None
        Humidity = None

    # Set wind direction to None if wind speed is zero
    if WindSpd[0] == 0:
        WindDir = [None,'degrees']

    # Extract required derived observations
    rainAccum = {'Today':     Obs['TodayRain'],
                 'Yesterday': Obs['YesterdayRain'],
                 'Month':     Obs['MonthRain'],
                 'Year':      Obs['YearRain']}
    avgWind   = Obs['AvgWind']
    maxGust   = Obs['MaxGust']

    # Calculate derived variables from SKY observations
    FeelsLike = derive.FeelsLike(Temp,Humidity,WindSpd,Config)
    RainRate  = derive.RainRate(Rain)
    rainAccum = derive.RainAccumulation(Rain,rainAccum,Device,Config)
    AvgWind   = derive.MeanWindSpeed(WindSpd,avgWind,Device,Config)
    MaxGust   = derive.MaxWindGust(WindGust,maxGust,Device,Config)
    WindSpd   = derive.BeaufortScale(WindSpd)
    WindDir   = derive.CardinalWindDirection(WindDir,WindSpd)
    UVIndex   = derive.UVIndex(UV)

    # Convert observation units as required
    RainRate      = observation.Units(RainRate,Config['Units']['Precip'])
    TodayRain     = observation.Units(rainAccum['Today'],Config['Units']['Precip'])
    YesterdayRain = observation.Units(rainAccum['Yesterday'],Config['Units']['Precip'])
    MonthRain     = observation.Units(rainAccum['Month'],Config['Units']['Precip'])
    YearRain      = observation.Units(rainAccum['Year'],Config['Units']['Precip'])
    WindSpd       = observation.Units(WindSpd,Config['Units']['Wind'])
    WindDir       = observation.Units(WindDir,Config['Units']['Direction'])
    WindGust      = observation.Units(WindGust,Config['Units']['Wind'])
    AvgWind       = observation.Units(AvgWind,Config['Units']['Wind'])
    MaxGust       = observation.Units(MaxGust,Config['Units']['Wind'])
    FeelsLike     = observation.Units(FeelsLike,Config['Units']['Temp'])

    # Define Kivy label binds
    Obs['FeelsLike']     = observation.Format(FeelsLike,'Temp')
    Obs['RainRate']      = observation.Format(RainRate,'Precip')
    Obs['TodayRain']     = observation.Format(TodayRain,'Precip')
    Obs['YesterdayRain'] = observation.Format(YesterdayRain,'Precip')
    Obs['MonthRain']     = observation.Format(MonthRain,'Precip')
    Obs['YearRain']      = observation.Format(YearRain,'Precip')
    Obs['WindSpd']       = observation.Format(WindSpd,'Wind')
    Obs['WindGust']      = observation.Format(WindGust,'Wind')
    Obs['AvgWind']       = observation.Format(AvgWind,'Wind')
    Obs['MaxGust']       = observation.Format(MaxGust,'Wind')
    Obs['WindDir']       = observation.Format(WindDir,'Direction')
    Obs['Radiation']     = observation.Format(Radiation,'Radiation')
    Obs['Battery']       = observation.Format(Battery,'Battery')
    Obs['UVIndex']       = observation.Format(UVIndex,'UV')

    # Return Station observations
    return Obs

def outdoorAir(Msg,Obs,Config):

    """ Handles Websocket messages received from outdoor AIR module

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Replace missing observations in latest outdoor AIR Websocket JSON with NaN
    Ob = [x if x != None else NaN for x in Msg['obs'][0]]

    # Extract outdoor AIR device ID
    Device = Config['Station']['OutAirID']

    # Extract required observations from latest outdoor AIR Websocket JSON
    Time     = [Ob[0],'s']
    Pres     = [Ob[1],'mb']
    Temp     = [Ob[2],'c']
    Humidity = [Ob[3],' %']
    Battery  = [Ob[6],' v']
    Strikes  = [Ob[4],'count']

    # Extract lightning strike data from the latest AIR Websocket JSON
    # "Summary" object
    StrikeTime = [Msg['summary']['strike_last_epoch'] if 'strike_last_epoch' in Msg['summary'] else NaN,'s']
    StrikeDist = [Msg['summary']['strike_last_dist']  if 'strike_last_dist'  in Msg['summary'] else NaN,'km']
    Strikes3hr = [Msg['summary']['strike_count_3h']   if 'strike_count_3h'   in Msg['summary'] else NaN,'count']

    # Extract required derived observations
    minPres      = Obs['MinPres']
    maxPres      = Obs['MaxPres']
    minTemp      = Obs['outTempMin']
    maxTemp      = Obs['outTempMax']
    StrikeCount  = {'Today': Obs['StrikesToday'],
                    'Month': Obs['StrikesMonth'],
                    'Year':  Obs['StrikesYear']}

    # Request Outdoor AIR data from the previous three hours
    Data3h = requestAPI.weatherflow.Last3h(Device,Time[0],Config)

    # Store latest Outdoor AIR Websocket message
    Obs['outAirMsg'] = Msg

    # Extract required observations from latest SKY Websocket JSON
    if 'SkyMsg' in Obs:
        Ob = [x if x != None else NaN for x in Obs['SkyMsg']['obs'][0]]
        WindSpd = [Ob[5],'mps']
    else:
        WindSpd = None

    # Calculate derived variables from AIR observations
    DewPoint         = derive.DewPoint(Temp,Humidity)
    SLP              = derive.SLP(Pres,Config)
    PresTrend        = derive.SLPTrend(Pres,Time,Data3h,Config)
    FeelsLike        = derive.FeelsLike(Temp,Humidity,WindSpd,Config)
    MaxTemp, MinTemp = derive.TempMaxMin(Time,Temp,maxTemp,minTemp,Device,Config)
    MaxPres, MinPres = derive.SLPMaxMin(Time,Pres,maxPres,minPres,Device,Config)
    StrikeCount      = derive.StrikeCount(Strikes,StrikeCount,Device,Config)
    StrikeFreq       = derive.StrikeFrequency(Time,Data3h,Config)
    StrikeDeltaT     = derive.StrikeDeltaT(StrikeTime)

    # Convert observation units as required
    Temp        = observation.Units(Temp,Config['Units']['Temp'])
    MaxTemp     = observation.Units(MaxTemp,Config['Units']['Temp'])
    MinTemp     = observation.Units(MinTemp,Config['Units']['Temp'])
    DewPoint    = observation.Units(DewPoint,Config['Units']['Temp'])
    FeelsLike   = observation.Units(FeelsLike,Config['Units']['Temp'])
    SLP         = observation.Units(SLP,Config['Units']['Pressure'])
    MaxPres     = observation.Units(MaxPres,Config['Units']['Pressure'])
    MinPres     = observation.Units(MinPres,Config['Units']['Pressure'])
    PresTrend   = observation.Units(PresTrend,Config['Units']['Pressure'])
    StrikeDist  = observation.Units(StrikeDist,Config['Units']['Distance'])

    # Define AIR Kivy label binds
    Obs['outTemp']      = observation.Format(Temp,'Temp')
    Obs['outTempMax']   = observation.Format(MaxTemp,'Temp')
    Obs['outTempMin']   = observation.Format(MinTemp,'Temp')
    Obs['DewPoint']     = observation.Format(DewPoint,'Temp')
    Obs['FeelsLike']    = observation.Format(FeelsLike,'Temp')
    Obs['Pres']         = observation.Format(SLP,'Pressure')
    Obs['MaxPres']      = observation.Format(MaxPres,'Pressure')
    Obs['MinPres']      = observation.Format(MinPres,'Pressure')
    Obs['PresTrend']    = observation.Format(PresTrend,'Pressure')
    Obs['StrikeDeltaT'] = observation.Format(StrikeDeltaT,'TimeDelta')
    Obs['StrikeDist']   = observation.Format(StrikeDist,'StrikeDistance')
    Obs['StrikeFreq']   = observation.Format(StrikeFreq,'StrikeFrequency')
    Obs['Strikes3hr']   = observation.Format(Strikes3hr,'StrikeCount')
    Obs['StrikesToday'] = observation.Format(StrikeCount['Today'],'StrikeCount')
    Obs['StrikesMonth'] = observation.Format(StrikeCount['Month'],'StrikeCount')
    Obs['StrikesYear']  = observation.Format(StrikeCount['Year'],'StrikeCount')
    Obs['Humidity']     = observation.Format(Humidity,'Humidity')
    Obs['Battery']      = observation.Format(Battery,'Battery')

    # Return Station observations
    return Obs

def indoorAir(Msg,Obs,Config):

    """ Handles Websocket messages received from indoor AIR module

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Replace missing observations in latest AIR Websocket JSON with NaN
    Ob = [x if x != None else NaN for x in Msg['obs'][0]]

    # Extract indoor AIR device ID
    Device = Config['Station']['InAirID']

    # Extract required observations from latest indoor AIR Websocket JSON
    Time     = [Ob[0],'s']
    Temp     = [Ob[2],'c']

    # Store latest indoor AIR Websocket message
    Obs['inAirMsg'] = Msg

    # Extract required derived observations
    minTemp = Obs['inTempMin']
    maxTemp = Obs['inTempMax']

    # Calculate derived variables from indoor AIR observations
    MaxTemp, MinTemp = derive.TempMaxMin(Time,Temp,maxTemp,minTemp,Device,Config)

    # Convert observation units as required
    Temp    = observation.Units(Temp,Config['Units']['Temp'])
    MaxTemp = observation.Units(MaxTemp,Config['Units']['Temp'])
    MinTemp = observation.Units(MinTemp,Config['Units']['Temp'])

    # Define indoor AIR Kivy label binds
    Obs['inTemp']    = observation.Format(Temp,'Temp')
    Obs['inTempMax'] = observation.Format(MaxTemp,'Temp')
    Obs['inTempMin'] = observation.Format(MinTemp,'Temp')

    # Return Station observations
    return Obs

def rapidWind(Msg,Obs,Config):

    """ Handles RapidWind Websocket messages received from either SKY or TEMPEST
        modules

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Replace missing observations from Rapid Wind Websocket JSON
    # with NaN
    Ob = [x if x != None else NaN for x in Msg['ob']]

    # Extract observations from latest Rapid Wind Websocket JSON
    Time    = [Ob[0],'s']
    WindSpd = [Ob[1],'mps']
    WindDir = [Ob[2],'degrees']

    # Extract wind direction from previous SKY Rapid-Wind Websocket JSON
    if 'RapidMsg' in Obs:
        Ob = [x if x != None else NaN for x in Obs['RapidMsg']['ob']]
        WindDirOld = [Ob[2],'degrees']
    else:
        WindDirOld = [0,'degrees']

    # If windspeed is zero, freeze direction at last direction of non-zero wind
    # speed and edit latest Rapid Wind Websocket JSON. Calculate wind shift
    if WindSpd[0] == 0:
        WindDir = WindDirOld
        Msg['ob'][2] = WindDirOld[0]

    # Store latest Rapid Wind Observation JSON message
    Obs['RapidMsg'] = Msg

    # Calculate derived variables from Rapid Wind observations
    WindDir = derive.CardinalWindDirection(WindDir,WindSpd)

    # Convert observation units as required
    WindSpd = observation.Units(WindSpd,Config['Units']['Wind'])
    WindDir = observation.Units(WindDir,'degrees')

    # Define Rapid Wind Kivy label binds
    Obs['rapidShift'] = WindDir[0] - WindDirOld[0]
    Obs['rapidSpd']   = observation.Format(WindSpd,'Wind')
    Obs['rapidDir']   = observation.Format(WindDir,'Direction')

    # Return Station observations
    return Obs

def evtStrike(Msg,Obs,Config):

    """ Handles lightning strike event Websocket messages received from AIR
        module

	INPUTS:
		Msg				    Websocket messages received from SKY module
		Obs			        Dictionary containing Station observations
        Config              Station configuration
	"""

    # Extract required observations from latest evt_strike Websocket JSON
    StrikeTime = [Msg['evt'][0],'s']
    StrikeDist = [Msg['evt'][1],'km']

    # Store latest Rapid Wind Observation JSON message
    Obs['evtStrikeMsg'] = Msg

    # Calculate derived variables from evt_strike observations
    StrikeDeltaT = derive.StrikeDeltaT(StrikeTime)

    # Convert observation units as required
    StrikeDist = observation.Units(StrikeDist,Config['Units']['Distance'])

    # Define AIR Kivy label binds
    Obs['StrikeDeltaT'] = observation.Format(StrikeDeltaT,'TimeDelta')
    Obs['StrikeDist']   = observation.Format(StrikeDist,'StrikeDistance')

    # Return Station observations
    return Obs