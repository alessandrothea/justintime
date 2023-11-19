from itertools import groupby
import datetime
import rich
import numpy as np
import logging
import collections
from .cruncher import signal

from rawdatautils.unpack.dataclasses import dts_to_datetime

class TriggerRecordCache:
    
    max_cache_size = 10
    
    def __init__(self, engine):
        self.engine = engine
        self.raw_data_files = {}
        self.tr_age = []
        self.shown_plots = []

    def update_shown_plots(self, new_shown_plots):
        self.shown_plots = new_shown_plots

    def get_trigger_record_data(self, trigger_record, raw_data_file):
        try:
            tr = self.raw_data_files[raw_data_file][trigger_record]
            # Mark tr as fresh
            i = self.tr_age.index( (raw_data_file, trigger_record) )
            self.tr_age.insert(0, self.tr_age.pop(i))
            return tr
        except KeyError:
            pass

        return self.add_trigger_record_to_file(trigger_record, raw_data_file)
            

    def add_trigger_record_to_file(self, trigger_record, raw_data_file):
        logging.debug(f"Adding {raw_data_file} {trigger_record}")

        self.raw_data_files.setdefault(raw_data_file,{})[trigger_record] = TriggerRecordData(self.engine, trigger_record, raw_data_file)

        self.tr_age.insert(0, (raw_data_file, trigger_record) )
        # Clear the cache if needed
        logging.debug(f"Current cache size = {len(self.tr_age)}, watermark = {self.max_cache_size}")
        if len(self.tr_age) > self.max_cache_size:
            old_rdf, old_tr = self.tr_age.pop()
            logging.debug(f"Clearing cache {old_rdf}, {old_tr}")

            del self.raw_data_files[old_rdf][old_tr]
            if len(self.raw_data_files[old_rdf]) == 0:
                del self.raw_data_files[old_rdf]

        l = 0
        for f in self.raw_data_files.values():
            l += len(f)
        logging.debug(f"Current Cache size: {l}")
        return self.raw_data_files[raw_data_file][trigger_record]



class TriggerRecordData:
    
    def __init__(self, engine, trigger_record, raw_data_file):
        self.engine     = engine
        self.df_dict    = engine.load_entry(raw_data_file, int(trigger_record))
        self.keys       = self.df_dict.keys()
        self.data_key   = f"detd_k{self.engine.det_name}_kWIBEth"
        self.run        = self.df_dict["trh"].index[0][0].astype(float)
        self.trigger    = self.df_dict["trh"].index[0][1].astype(float)
        
        indexies = np.array(self.df_dict["trh"].index[0]).astype(int)

        print("\n"*5)
        print(type(self.df_dict["trh"].index[0][0]))
        print(self.df_dict["trh"].index[0][0])
        print(self.df_dict["trh"].index[0][1])
        print("\n"*5)
        
        self.run        = indexies[0]
        self.trigger    = indexies[1]

        logging.info(f"Trigger timestamp (ticks): {self.get_trigger_ts()}")
        logging.info(f"Trigger timestamp (sec from epoc): {dts_to_datetime(self.get_trigger_ts()).strftime('%b-%d-%Y, %H:%M:%S')}")

    def get_trigger_ts(self):
        return self.df_dict['trh'].trigger_timestamp_dts.iloc[0]

    def get_adcs_per_planes(self, key=None):
        
        if key is None:
            return (self.df_dict[self.data_key].query("plane == 0"),
                    self.df_dict[self.data_key].query("plane == 1"),
                    self.df_dict[self.data_key].query("plane == 2"))
        else:
            return (self.df_dict[self.data_key].query("plane == 0")[key],
                    self.df_dict[self.data_key].query("plane == 1")[key],
                    self.df_dict[self.data_key].query("plane == 2")[key])









        """
        self.info, self.df, self.tp_df = engine.load_entry(raw_data_file, int(trigger_record)) #, self.ta_df, self.tc_df 

        self.tr_ts = self.info['trigger_timestamp']
        self.tr_ts_sec = self.tr_ts/int(62e6) 
        logging.info(f"Trigger timestamp (ticks): {self.tr_ts}")
        logging.info(f"Trigger timestamp (sec from epoc): {self.tr_ts_sec}")
        try:
            self.tr_ts_date = datetime.datetime.fromtimestamp(self.tr_ts_sec).strftime('%c')
        except ValueError:
            self.tr_ts_date = 'Invalid'
        logging.info(f"Trigger date: {self.tr_ts_date}")


        self.ts_min = self.df.index.min()
        self.ts_max = self.df.index.max()

        if self.tr_ts != 0xffffffffffffffff:
            self.ts_off = self.tr_ts 
        else:
            logging.warning("Invalid trigger TS detected!!!")
            logging.info("Using tmax-tmin as trigger timestamp")
            self.ts_off = int((self.ts_max+self.ts_min)//2)
            
        logging.info(f"Timestamp offset: {self.ts_off}")

        self.df_tsoff = self.df.copy()    
        self.df_tsoff.index=self.df_tsoff.index.astype('int64')-self.ts_off
        self.channels = list(self.df_tsoff.columns)

        self.planes = {}
        for ch in self.channels:
            p = engine.ch_map.get_plane_from_offline_channel(int(ch))
            self.planes.setdefault(p, []).append(ch)

        self.safe_planes = {k:sorted(set(v) & set(self.df_tsoff.columns)) for k,v in self.planes.items()}

        self.df_U =  self.df_tsoff[self.safe_planes.get(0, [])]
        self.df_V =  self.df_tsoff[self.safe_planes.get(1, [])]
        self.df_Z =  self.df_tsoff[self.safe_planes.get(2, [])]

        self.df_U_mean, self.df_U_std = self.df_U.mean(), self.df_U.std()
        self.df_V_mean, self.df_V_std = self.df_V.mean(), self.df_V.std()
        self.df_Z_mean, self.df_Z_std = self.df_Z.mean(), self.df_Z.std()

        self.fft_phase = {}

        # Save planes boundaries
        self.xmin_U = min(self.planes.get(0,{}),default=0)
        self.xmax_U = max(self.planes.get(0,{}),default=0)
        self.xmin_V = min(self.planes.get(1,{}),default=0)
        self.xmax_V = max(self.planes.get(1,{}),default=0)
        self.xmin_Z = min(self.planes.get(2,{}),default=0)
        self.xmax_Z = max(self.planes.get(2,{}),default=0)
        self.xmin_O = min(self.planes.get(9999,{}),default=0)
        self.xmax_O = max(self.planes.get(9999,{}),default=0)


    def find_plane(self, offch):
        m={0:'U', 1:'V', 2:'Z'}
        p = self.engine.ch_map.get_plane_from_offline_channel(offch)
        if p in m:
            return m[p]
        else:
            return 'D'

    def init_fft(self):
        try: self.df_fft
        except AttributeError: 
            self.df_fft = signal.calc_fft_fft_sq(self.df_tsoff)[1]

    def init_fft2(self):
        try: self.df_fft2
        except AttributeError: self.df_fft2 = signal.calc_fft_sum_by_plane(self.df_tsoff, self.planes)
        try: self.df_U_plane
        except AttributeError: self.df_U_plane = self.df_fft2['U-plane']
        try: self.df_V_plane
        except AttributeError: self.df_V_plane = self.df_fft2['V-plane']
        try: self.df_Z_plane
        except AttributeError: self.df_Z_plane = self.df_fft2['Z-plane']

    def init_fft_phase(self, fmin, fmax):
        try: self.df_fft
        except AttributeError: self.df_fft = signal.calc_fft(self.df_tsoff)
        try: self.fft_phase[f"{fmin}-{fmax}"]
        except KeyError:

            self.fft_phase[f"{fmin}-{fmax}"] = signal.calc_fft_phase(self.df_fft, fmin, fmax)
            print(self.fft_phase[f"{fmin}-{fmax}"])
            self.fft_phase[f"{fmin}-{fmax}"]['femb']  = self.fft_phase[f"{fmin}-{fmax}"].index.map(self.engine.femb_id_from_offch)
            self.fft_phase[f"{fmin}-{fmax}"]['plane'] = self.fft_phase[f"{fmin}-{fmax}"].index.map(self.find_plane)                
    

    def init_tp(self):
        self.tp_df_tsoff = self.tp_df.copy()
        self.tp_df_tsoff['time_peak'] = (self.tp_df_tsoff['time_peak'].astype('int64')-self.ts_off)
        self.tp_df_tsoff['time_start'] = (self.tp_df_tsoff['time_start'].astype('int64')-self.ts_off)

        # self.tp_df_U = self.tp_df_tsoff[self.tp_df_tsoff['channel'].isin(self.planes.get(0, {}))]
        # self.tp_df_V = self.tp_df_tsoff[self.tp_df_tsoff['channel'].isin(self.planes.get(1, {}))]
        # self.tp_df_Z = self.tp_df_tsoff[self.tp_df_tsoff['channel'].isin(self.planes.get(2, {}))]
        # self.tp_df_O = self.tp_df_tsoff[self.tp_df_tsoff['channel'].isin(self.planes.get(9999, {}))]

        self.tp_df_U = self.tp_df_tsoff[self.tp_df_tsoff['plane'] == 0]
        self.tp_df_V = self.tp_df_tsoff[self.tp_df_tsoff['plane'] == 1]
        self.tp_df_Z = self.tp_df_tsoff[self.tp_df_tsoff['plane'] == 2]
        self.tp_df_O = self.tp_df_tsoff[self.tp_df_tsoff['plane'] == 9999]


        # print(self.tp_df_Z)

    """

    """def init_ta(self):
        self.ta_df_tsoff = self.ta_df.copy()
        for c in ('time_start', 'time_end', 'time_peak', 'time_activity'):
            self.ta_df_tsoff[c] = (self.ta_df_tsoff[c].astype('int64')-self.ts_off)

        # self.ta_df_U = self.ta_df_tsoff[self.ta_df_tsoff['channel_peak'].isin(self.planes.get(0, {}))]
        # self.ta_df_V = self.ta_df_tsoff[self.ta_df_tsoff['channel_peak'].isin(self.planes.get(1, {}))]
        # self.ta_df_Z = self.ta_df_tsoff[self.ta_df_tsoff['channel_peak'].isin(self.planes.get(2, {}))]
        # self.ta_df_O = self.ta_df_tsoff[self.ta_df_tsoff['channel_peak'].isin(self.planes.get(9999, {}))]
        
        self.ta_df_U = self.ta_df_tsoff[self.ta_df_tsoff['plane'] == 0]
        self.ta_df_V = self.ta_df_tsoff[self.ta_df_tsoff['plane'] == 1]
        self.ta_df_Z = self.ta_df_tsoff[self.ta_df_tsoff['plane'] == 2]
        self.ta_df_O = self.ta_df_tsoff[self.ta_df_tsoff['plane'] == 9999]
        
    """
    # def init_fft_phase_22(self):
    #     try: self.df_fft
    #     except AttributeError: self.df_fft = signal.calc_fft(self.df)
    #     fmin = 21000
    #     fmax = 24000
    #     try: self.df_phase_22
    #     except AttributeError: 
    #         self.df_phase_22 = signal.calc_fft_phase(self.df_fft, fmin, fmax)
    #         self.df_phase_22['femb']  = self.df_phase_22.index.map(self.engine.femb_id_from_offch)
    #         self.df_phase_22['plane'] = self.df_phase_22.index.map(self.find_plane)

    # def init_fft_phase_210(self):
    #     try: self.df_fft
    #     except AttributeError: self.df_fft = signal.calc_fft(self.df)
    #     fmin = 129000
    #     fmax = 220000
    #     try: self.df_phase_210
    #     except AttributeError: 
    #         self.df_phase_210 = signal.calc_fft_phase(self.df_fft, fmin, fmax)
    #         self.df_phase_210['femb']  = self.df_phase_210.index.map(self.engine.femb_id_from_offch)
    #         self.df_phase_210['plane'] = self.df_phase_210.index.map(self.find_plane)

    # def init_fft_phase_430(self):
    #     try: self.df_fft
    #     except AttributeError: self.df_fft = signal.calc_fft(self.df)
    #     fmin=405000
    #     fmax=435000
    #     try: self.df_phase_430
    #     except AttributeError: 
    #         self.df_phase_430 = signal.calc_fft_phase(self.df_fft, fmin, fmax)
    #         self.df_phase_430['femb']  = self.df_phase_430.index.map(self.engine.femb_id_from_offch)
    #         self.df_phase_430['plane'] = self.df_phase_430.index.map(self.find_plane)
    """
    def init_cnr(self):
        try: self.df_cnr
        except AttributeError: 
            self.df_cnr = self.df_tsoff.copy()
            self.df_cnr = self.df_cnr-self.df_cnr.mean()
            for p, p_chans in self.planes.items():
                for f,f_chans in self.engine.femb_to_offch.items():
                    chans = list(set(p_chans) & set(f_chans))
                    self.df_cnr[chans] = self.df_cnr[chans].sub(self.df_cnr[chans].mean(axis=1), axis=0)
    """