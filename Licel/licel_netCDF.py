import numpy as np
import netCDF4 
from datetime import datetime, timezone
import time
import os 

class Licel_Netcdf_Wrapper():

    #: netcdf filename
    filename = ""
    #: netcdf Dataset
    Dataset = "" 

    #: netcdf variable holding which user is logged into the operating system
    os_user = ""
    #: netcdf variable holding operating system info
    os_info = ""
    #: netcdf variable holding python API version
    wind_version = ""
    #: netcdf variable holding waverider Hardware version
    waverider_version = ""
    #: netcdf variable holding wind lidar station name.
    station_name = ""
    #: netcdf variable holding wind lidar latitude
    station_lat = 0.0 
    #: netcdf variable holding wind lidar longitude
    station_long = 0.0 
    #: netcdf variable holding wind lidar altitude
    station_alt = 0.0
    #: netcdf variable holding wind lidar azimuth
    azimuth = 0.0 
    #: netcdf variable holding wind lidar zenith 
    zenith = 0.0 
    #: netcdf variable holding wind lidar maximal distance range
    max_distance = 0.0
    #: netcdf variable holding wind lidar range resolution 
    range_resolution = 0.0
    #: netcdf variable holding wind lidar timing resolution
    time_resolution = 0.0
    #: netcdf variable holding wind lidar frequency increment  
    freqeuncy_increment = 0.0
    #: netcdf variable holding waverider ADC sampling rate
    waverider_sample_rate = 0.0
    #: netcdf variable holding trigger names
    trigger_names = 0
    #: netcdf variable holding target shots we want to acquire
    target_shots = 0
    #: netcdf variable holding fft size
    fft_size = 0
    #: netcdf variable holding index at which our first record in the file start,
    #:  this variable is needed for compatibility reason with the Labview version.
    first_record = 0

    def __init__(self, filename, access_mode, device, numFFT, FFTSize, numTrig):
        '''

        When initializing the class Licel_Netcdf_Wrapper, we create the netcdf
        data structure which will hold the metainformation and powerspectra 
        of our acquisition. 

        :param filename: filename to write the netcdf data to.
                         if no file exist, a new file will be created.
                         if the file exist, it will be overwritten.
        :type filename: str

        :param access_mode: defined the file access mode, the usual "read, write"
        :type access_mode: str, "w", "r" "rw"

        :param device: The device we acquire the data from,
                       currently only waverider is supported. device should be "Waverider"
        :type device: str

        :param numFFT: number of fft to be calculated.
        :type numFFT: int

        :param FFTSize: Number of ADC samples that goes into computing a single fft.
        :type FFTSize: int

        :param numTrig: number of trigger , currently only single trigger is supported.
        :type numTrig: int
        '''
        self.filename = filename
        self.accessmode = access_mode
        self.numFFT = numFFT
        self.FFT_Size = FFTSize
        self.numTrig = numTrig

        if device == "Waverider": 
            if numTrig != 1:
                raise RuntimeError("currently supports only single trigger wind\r\n")
            self.Dataset = self.createNetCDF_Wind_Structure()
            self._fillGlobalAttribuite()
            self.createVarDescription()
        elif device == "Transient": 
            self.Dataset = self.fillTransientDataset()
        else : 
            raise RuntimeError(device,"is not a supported device \r\n")

    def createNetCDF_Wind_Structure(self) -> netCDF4.Dataset:
        '''
        populate the Netcdf File structure. 
        Here we will  define the skeleton of the Netcdf file without giving any variable value
        we also add descriptions for each variable.

        :return: structure holding the netcdf data set.
        :rtype: netCDF4.Dataset
        '''
        
        Dataset = netCDF4.Dataset(self.filename, self.accessmode, 'NETCDF4')
        self.time_dim = Dataset.createDimension("time", None) # unlimited dimension
        Dataset.createDimension("num_trigger", self.numTrig)
        Dataset.createDimension("num_fft", self.numFFT)
        # TODO : fft_size_dim is actually the size of the powerspectra
        # to conserve compatibility with the Labview viewer the name remains unchanged. 
        # PowerSpectra_dim = fft_size / 2
        Dataset.createDimension("fft_size_dim", self.FFT_Size/2) 
        Dataset.createDimension('max_slen', 200)

        self.os_user = Dataset.createVariable("os_user",
                                            datatype= 'S1', dimensions = ('max_slen'))
        self.os_info = Dataset.createVariable("os_info",
                                    datatype= 'S1', dimensions = ('max_slen'))
        self.wind_version = Dataset.createVariable("wind_version",
                            datatype= 'S1', dimensions = ('max_slen'))
        self.waverider_version = Dataset.createVariable("waverider_version",
                            datatype= 'S1', dimensions = ('max_slen'))
        self.netcdf_file_name = Dataset.createVariable("file_name",
                            datatype= 'S1', dimensions = ('max_slen'))
        self.station_name = Dataset.createVariable("station_name",
                    datatype= 'S1', dimensions = ('max_slen'))
        self._createStationCoordinateVariable(Dataset)
        self._createWaveriderVaraiables(Dataset)

        return Dataset
    
    def fillAcquisitionInfo(self, max_distance, samplingRate_hz, targetShots,
                        FFT_Size, wind):
        '''
        fill information related to the Acquisition.

        :param max_distance: maximum distance range to be acquired in meters.
        :type max_distance: int

        :param samplingRate_hz: the waverider ADC sampling rate in hertz.
        :type samplingRate_hz: int

        :param targetShots: the target shots to be acquired in a single acquisition.
        :type targetShots: int

        :param FFT_Size: number of ADC sample that goes into a single FFT.
        :type FFT_Size: int

        :param wind: the waverider python object. 
        :type wind: licel_wind.Waverider 
        '''

        self.writeString(self.trigger_names,"Trig1")
        rangeRes = wind.calcLidarRangeResolution(samplingRate_hz, FFT_Size)
        timeRes  = wind.calcTimeResolution(samplingRate_hz, FFT_Size)
        freqeuncy_increment = wind.calcFrequencyIncrement(samplingRate_hz, FFT_Size)
        self.max_distance[:] = max_distance
        self.range_resolution[:] = rangeRes
        self.time_resolution[:] = timeRes
        self.freqeuncy_increment[:] = freqeuncy_increment
        self.waverider_sample_rate[:] = samplingRate_hz
        self.target_shots[:] = targetShots
        self.fft_size[:] = FFT_Size

    def _fillGlobalAttribuite(self):
        '''
        fill Netcdf global attribuite.
        '''
        self.Dataset.title = "Licel WIND"
        self.Dataset.format_date = "2024-06-21"
        self.Dataset.format_version = 0.1
        self.Dataset.history = "Licel WIND V2"
        self.Dataset.creation_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        username = os.environ.get('USER', os.environ.get('USERNAME')) 
        self.writeString(self.os_user,username)
        self.writeString(self.os_info,os.name)
        self.writeString(self.wind_version,"Python V0.1")
        self.writeString(self.waverider_version,"Firmware rev. 2")
        self.writeString(self.netcdf_file_name,self.filename)

    def fillGeoPositionInfo(self, stationName:str, latitude: float,
                             longitude: float, altitude: float,
                             azimuth: float, zenith: float):
        
        '''
        write the geographical position information to the netcdf file.

        :param stationName: the location name where the acquisition is taking place.
        :type stationName: str

        :param latitude: Geographical latitude of the wind lidar (degrees_north)
        :type  latitude: float

        :param longitude: Geographical latitude of the wind lidar (degrees_east)
        :type  longitude: float

        :param altitude: Altitude above sea level of the wind lidar (kilometers)
        :type  altitude: float

        :param azimuth: Azimuth angle of the wind lidar in degrees
        :type azimuth: float

        :param zenith: Zenith angle of the wind lidar in degrees
        :type zenith: float
        
        '''
        self.station_lat[:] = latitude
        self.station_long[:] = longitude
        self.station_alt[:] = altitude
        self.azimuth[:] = azimuth
        self.zenith[:] = zenith
        self.writeString(self.station_name,stationName)
    
    def fillTransientDataset(self) ->  netCDF4.Dataset: 
        Dataset = netCDF4.Dataset(self.filename, self.accessmode, 'NETCDF4')
        print("Work in progress ...")
        print("Support for Transient Recorder NetCDF planned for the up " \
              "coming release ...")
        return Dataset

    def writeString(self, NetCDF_var, Var_string):
        '''
        helper function to write strings to netcdf file.

        :param NetCDF_var: netCDF variable to be written to.
        :type NetCDF_var: netCDF4.variable(str)

        :param Var_string: string to be written to netcdf variable. maxlength is 200 char.
        :type Var_string: str
        '''
        tmp = np.array([Var_string],dtype='S200')
        NetCDF_var[:] = netCDF4.stringtochar(tmp)

    def printVar(self, NetCDF_var):
        '''
        helper function to print netcdf variables.

        :param NetCDF_var: netcdf variable to be printed to console
        :type NetCDF_var: netCDF4.variable
        '''
        print(NetCDF_var[:])

    def _createStationCoordinateVariable(self, Dataset):
        '''
        helper function to create netcdf structure holding geographical 
        position information 

        :param Dataset: Netcdf datastructe that needs to be filled.
        :type Dataset: netCDF4.Dataset
        '''
        self.station_lat = Dataset.createVariable("station_lat",
                    datatype= "f8", fill_value = 1)
        self.station_long = Dataset.createVariable("station_long",
                    datatype= "f8", fill_value = 2)
        self.station_alt = Dataset.createVariable("station_alt",
                    datatype= "f8", fill_value = 3)
        self.azimuth = Dataset.createVariable("azimuth",
                    datatype= "f8", fill_value = 4) 
        self.zenith = Dataset.createVariable("zenith",
                    datatype= "f8", fill_value = 5)

    def _createWaveriderVaraiables(self, Dataset):
        '''
        helper function to create variables structure holding the 
        waverider and acquisition information, including the Dataset structure.

        :param Dataset: Netcdf datastructures that needs to be filled.
        :type Dataset: netCDF4.Dataset
        '''
        self.max_distance = Dataset.createVariable("max_distance",
            datatype= "f8", fill_value = 0)
        
        self.range_resolution = Dataset.createVariable("range_resolution",
            datatype= "f8", fill_value = 0)
        
        self.time_resolution = Dataset.createVariable("time_resolution",
            datatype= "f8", fill_value = 0)
        
        self.freqeuncy_increment = Dataset.createVariable("frequncy_increment",
            datatype= "f8", fill_value = 0) 
        
        self.waverider_sample_rate = Dataset.createVariable("waverider_sample_rate",
            datatype= "f8", fill_value = 0)
        
        self.trigger_names = Dataset.createVariable("trigger_names",
            datatype= "S1", dimensions = ('num_trigger', 'max_slen')) 
        
        ########################################################################
        self.target_shots = Dataset.createVariable("target_shots",
            datatype= 'u4', fill_value = 0) 
        
        self.fft_size = Dataset.createVariable("fft_size",
            datatype= 'u4', fill_value = 0) 
        
        self.first_record = Dataset.createVariable("first_record",
            datatype= 'u4', fill_value = 0) 
        
        self.timestamp_start = Dataset.createVariable("timestamp_start",
            datatype= 'u4', fill_value = 0)
         
        self.current_record = Dataset.createVariable("current_record",
            datatype= 'u4',  dimensions = ('time')) 
        
        self.timestamp_record = Dataset.createVariable("timestamp_record",
            datatype= 'u4', dimensions = ('time'), fill_value = 0)
         
        self.pc_time_start = Dataset.createVariable("pc_time_start",
            datatype= 'f8', fill_value = 0) 
        
        self.pc_time_read = Dataset.createVariable("pc_time_read",
            datatype= 'f8', dimensions = ('time'), fill_value = 0) 
        
        #### Data ### 
        self.acquired_shots = Dataset.createVariable("acquired_shots",
            datatype= 'u8', fill_value = 0, dimensions = ('time', 'num_trigger')) 
        self.fft_data = Dataset.createVariable("fft_data",
            datatype= 'u8', dimensions = ('time' ,'num_trigger','num_fft', 'fft_size_dim')) 
      
    def createVarDescription(self): 
        '''
        helper function to create and write variable description in netcdf file.
        this information could be dumped using ncdump.exe 
        '''
        self.os_user.long_description	= "User login name at the operating system"
        self.os_info.long_description	= "Operating system information"
        
        self.wind_version.long_description	= "Software version of the wind acquisition software"
        self.waverider_version.long_description	= "Firmware version of the waverider"

        self.station_name.long_description	= "Name of the wind lidar station"
        self.trigger_names.long_description	= "Configurable trigger names"  

        self.station_lat.units			= "degrees_north"
        self.station_lat.valid_range		= (-90.0, 90.0)
        self.station_lat.long_description	= "Geographical latitude of the wind lidar"
        self.station_lat.C_format		= "%11.6f"

        self.station_long.units			= "degrees_east"
        self.station_long.valid_range   		= (-180.0, 180.0)
        self.station_long.long_description	= "Geographical longitude of the wind lidar"
        self.station_long.C_format		= "%11.6f"

        self.station_alt.units			= "kilometers"
        self.station_alt.valid_range		= (-430.0, 8850.0)
        self.station_alt.long_description	= "Altitude above sea level of the wind lidar"
        self.station_alt.C_format		= "%8.3f"
        
        self.azimuth.units               = "degrees" 
        self.azimuth.valid_range		= (0.0, 360.0)
        self.azimuth.long_description	= "Azimuth angle of the wind lidar"
        self.azimuth.C_format		= "%10.6f" 

        self.zenith.units               = "degrees" 
        self.zenith.valid_range		= (0.0, 90.0)
        self.zenith.long_description	= "Zenith angle of the wind lidar"
        self.zenith.C_format		= "%9.6f"

        self.max_distance.units               = "meters" 
        self.max_distance.valid_range		= (0.0, 20000.0)
        self.max_distance.long_description	= "Acquired Range"
        self.max_distance.C_format		= "%8.2f"
        
        self.range_resolution.units               = "meters" 
        self.range_resolution.valid_range		= (0.0, 100.0)
        self.range_resolution.long_description	= "Range increment"
        self.range_resolution.C_format		= "%6.2f"
        
        self.time_resolution.units               = "microseconds" 
        self.time_resolution.valid_range		= (0.0, 1000.0)
        self.time_resolution.long_description	= "Time increment"
        self.time_resolution.C_format		= "%7.2f"
        
        self.freqeuncy_increment.units               = "Hertz" 
        self.freqeuncy_increment.valid_range		= (0.0, 10.0)
        self.freqeuncy_increment.long_description	= "Frequency increment"
        self.freqeuncy_increment.C_format		= "%9.6f"

        self.waverider_sample_rate.units               = "MHz" 
        self.waverider_sample_rate.valid_range		= (0.0, 3200) 
        self.waverider_sample_rate.long_description	= "Sampling rate ate the waverider"
        self.waverider_sample_rate.C_format		= "%.1f"	

        self.target_shots.units               = "shots" 
        self.target_shots.valid_range		= (0, 10000) 
        self.target_shots.long_description	= "Number of shots/triggers"
        self.target_shots.C_format		= "%ld"
        
        self.fft_size.units               = "size" 
        self.fft_size.valid_range		= (64, 2048) 
        self.fft_size.long_description	= "FFT size"
        self.fft_size.C_format		= "%ld"
        
        self.first_record.units               = "index" 
        self.first_record.valid_range		= (0, 4294967295) 
        self.first_record.long_description	= "1st record index in a file"
        self.first_record.C_format		= "%ld"
        
        self.timestamp_start.units               = "Milliseconds" 
        self.timestamp_start.valid_range		= (0, 4294967295) 
        self.timestamp_start.long_description	= "Controller time stamp when starting the acquisition"
        self.timestamp_start.C_format		= "%ld"
        
        self.current_record.units               = "index" 
        self.current_record.valid_range		= (0, 4294967295) 
        self.current_record.long_description	= "record index of the current data set"
        self.current_record.C_format		= "%ld"

        self.timestamp_record.units               = "Milliseconds" 
        self.timestamp_record.valid_range		= (0, 4294967295) 
        self.timestamp_record.long_description	= "Controller time stamp of the current data set"
        self.timestamp_record.C_format		= "%ld"

        self.pc_time_start.units               = "Seconds" 
        self.pc_time_start.valid_range		= (0.0, 6185322000.0) 
        self.pc_time_start.long_description	= "PC time corresponding to timestamp_start, seconds since 12:00 a.m. 1904-01-01 UTC"
        self.pc_time_start.C_format		= "%.8f"
        
        self.pc_time_read.units               = "Seconds" 
        self.pc_time_read.valid_range		= (0.0, 6185322000.0) 
        self.pc_time_read.long_description	= "PC time corresponding to the submission current record, seconds since 12:00 a.m. 1904-01-01 UTC"
        self.pc_time_read.C_format		= "%.8f" 
        
        self.acquired_shots.units               = "shots" 
        self.acquired_shots.valid_range		= (0, 4294967295) 
        self.acquired_shots.long_description	= "Acquired shots" 
        self.acquired_shots.C_format = "%ld" 

        self.fft_data.units               = "VRMS^2" 
        self.fft_data.valid_range		= (0, 18446744073709551615) 
        self.fft_data.long_description	= "Acquired fft data" 
        self.fft_data.C_format		= "%lld" 
    
    def time_unix_to_epoch_1904(self):
        
        '''
        python time return the number of seconds since
        January 1, 1970, 00:00:00 (UTC) on all platforms.
        the netcdf epoch starts  since 12:00 a.m. 1904-01-01 UTC in in seconds.

        :return: time since the start of the epoch 1904 in seconds.
        :rtype: float
        ''' 
        
        epoch_delta = 2082844800  #in seconds 
        unix_time = time.time()
        netcdf_time = unix_time + epoch_delta
        return float(netcdf_time)
    
    def saveNetcdf(self,cycle, powerSpectra: np.ndarray[np.uint64],
                   timestamp: np.ndarray['1',np.uint64], currentShots: int):
        '''
        Save powerspectra data acquired from the waverider to the netcdf file.

        :param powerSpectra: powerspectra data to be saved
        :type powerSpectra: np.ndarray[np.uint64]

        :param timestamp: Waverider timestamp to be saved, in milliseconds.
        :param timestamp: np.ndarray['1',np.uint64]

        :param currentShots: acquired shots from the waverider.
        :type currentShots: int

        '''
        powerSpectra_size = self.FFT_Size / 2
        reshaped_powerSpectra = np.reshape(powerSpectra, (self.numFFT, int(powerSpectra_size)))
        self.timestamp_record[cycle:] = timestamp 
        self.current_record[cycle:] = cycle
        self.acquired_shots[cycle:] = currentShots
        self.Dataset.variables['fft_data'][cycle] = reshaped_powerSpectra
        print("timestamp:",self.current_record[:]) 