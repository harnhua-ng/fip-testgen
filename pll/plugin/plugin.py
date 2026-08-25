import numpy as np
# ------------------------------------------------
# common template for GUI attributes
# ------------------------------------------------
class gui_attr:
    def __init__ (self,options=(),
                       def_val=0,
                       usr_val=0,
                       editopt=1,
                       hideopt=0,
                       hidedsp=0,
                       atrname='gui_attr'
                 ):

        self.options = options
        self.def_val = def_val
        self.usr_val = def_val
        self.cal_val = def_val
        self.editopt = editopt
        self.hideopt = hideopt
        self.hidedsp = hidedsp
        self.atrname = atrname

    def set_attr_options(self,options):
        self.options = options

    def set_attr_default_value(self,def_val):
        self.def_val = def_val

    def set_attr_user_value(self,usr_val):
        self.usr_val = usr_val

    def set_attr_calc_value(self,cal_val):
        self.cal_val = cal_val

    def set_attr_editable(self,editopt=1):
        self.editopt = 'True' if(editopt) else 'False'

    def set_attr_hidden(self,hideopt=1,hidedsp=1):
        self.hideopt = 'True' if(hideopt) else 'False'
        self.hidedsp = 'True' if(hidedsp) else 'False'

    def get_attr_calc_value(self):
        return self.cal_val

    def get_val(self):
        return (self.usr_val if(self.editopt) else self.cal_val)

    def print_attr_values(self):
        print("[DEBUG] Name : {:25} : Edit: {:1} : Hide : {:1} : Def : {:<10} : Usr : {:<10} : Calc : {:<10} : Opts : {}".format(self.atrname,
              self.editopt,self.hideopt,self.def_val,self.usr_val,self.cal_val,self.options))

# ------------------------------------------------
# GPLL parameter class
# ------------------------------------------------
class GPLL_PARAM:
    from math  import log, log10, exp
    from cmath import phase
    from sys   import version
    from time  import perf_counter

    def __init__ (self):
        print("[INFO] Using Python version : %s" % self.version)
        self.np                                             = np
        # local handle for absolute value function
        self.abs                                            = abs
        self.round                                          = round

        self.rtl_params                                     = {}
        # Range/Limits specified in Tspec
        self.PARAM_RANGE                                    = {'FREF'        : {'MIN' : 18.0 , 'MAX' : 800.0 } # limited to 18 MHz based on PE char
                                                              ,'FPFD_I'      : {'MIN' : 18.0 , 'MAX' : 500.0 } # limited to 18 MHz based on PE char
                                                              ,'FPFD_F'      : {'MIN' : 18.0 , 'MAX' : 100.0 } # limited to 18 MHz based on PE char
                                                              ,'FPFD_JP'     : {'MIN' : 10.0 , 'MAX' : 160.0 } # for JP devices only
                                                              ,'FVCO'        : {'MIN' : 800.0, 'MAX' : 1600.0}
                                                              ,'FOUT_I'      : {'MIN' : 10.0 , 'MAX' : 800.0 }
                                                              ,'FOUT_F'      : {'MIN' : 6.25 , 'MAX' : 800.0 }
                                                              ,'M_DIV'       : {'MIN' : 1    , 'MAX' : 44    } # limit min PFD to 18 MHz
                                                              ,'N_DIV_I'     : {'MIN' : 1    , 'MAX' : 128   }
                                                              ,'N_DIV_F'     : {'MIN' : 16.0 , 'MAX' : 128.0 }
                                                              ,'O_DIV'       : {'MIN' : 1    , 'MAX' : 128   }
                                                              ,'FRAC_N'      : {'MIN' : 0    , 'MAX' : 4095  }
                                                              ,'PEAK'        : {'MIN' : 0.0  , 'MAX' : 1.20  }
                                                              ,'PM_3DB'      : {'MIN' : 45.0                 }
                                                              ,'BWFACTOR_LF' : {'MIN' : 0.0                  } # min BWFACTOR to use for PFD <= 100 MHz
                                                              ,'BWFACTOR_HF' : {'MIN' : 10.0                 } # min BWFACTOR to use for PFD > 100 MHz
                                                              }
        self.FRAC_N_MAX1                                    = 4096

        # max iterations to try
        self.N_ITER_MAX                                     = 20

        self.bypass_bw_factor                               = 0

        # -------------------------------------------------------------------------------------------------------------
        # GUI Attributes
        # -------------------------------------------------------------------------------------------------------------

        # ----------------------
        # General
        # ----------------------

        # Configuration Mode
        self.gui_config_mode                                = gui_attr(options=[('Frequency', 'FREQUENCY'),
                                                                                ('Divider'  , 'DIVIDER')],
                                                                       def_val='FREQUENCY',
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_config_mode')

        # Optimization Target
        self.gui_optim_prio                                 = gui_attr(options=[('Minimum Power (Lower VCO)', 'POWER' ),
                                                                                ('Minimum Jitter (Higher VCO)','JITTER')],
                                                                       def_val='JITTER',
                                                                       editopt=0,
                                                                       hideopt=0,
                                                                       atrname='gui_optim_prio')

        # Enable Fractional-N Divider
        self.gui_en_frac_n                                  = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_frac_n')

        # Enable Spread Spectrum Clock
        self.gui_en_ssc                                     = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_ssc')

        # Enable User Feedback clock
        self.gui_en_usr_fbk                                 = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_usr_fbk')

        # Enable PMU wait for PLL Lock
        self.gui_en_pmu_wait_lock                           = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=1,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_en_pmu_wait_lock')

        # Enable Internal Path Swithing
        self.gui_en_int_fbkdel_sel                          = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_int_fbkdel_sel')

        # Actual VCO frequency - to be recalculated later
        self.gui_vco_freq                                   = gui_attr(options=(self.PARAM_RANGE['FVCO']['MIN'],
                                                                                self.PARAM_RANGE['FVCO']['MAX']),
                                                                       def_val=self.PARAM_RANGE['FVCO']['MIN'],
                                                                       editopt=0,
                                                                       hideopt=0,
                                                                       atrname='gui_vco_freq')

        # ----------------------
        # Reference Clock
        # ----------------------

        # Reference Clock Frequency
        self.gui_refclk_freq                                = gui_attr(options=(self.PARAM_RANGE['FREF']['MIN'],
                                                                                self.PARAM_RANGE['FREF']['MAX']),
                                                                       def_val=100.0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_refclk_freq')

        # Reference clock divider - to be recalculated later
        self.gui_m_div                                      = gui_attr(options=(self.PARAM_RANGE['M_DIV']['MIN'],
                                                                                self.PARAM_RANGE['M_DIV']['MAX']),
                                                                       def_val=self.PARAM_RANGE['M_DIV']['MIN'],
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       hidedsp=0,
                                                                       atrname='gui_m_div')

        # Phase detector frequency
        self.gui_phasedet_freq                              = gui_attr(options=(self.PARAM_RANGE['FPFD_I']['MIN'],
                                                                                self.PARAM_RANGE['FPFD_I']['MAX']),
                                                                       def_val=(1.0*self.gui_refclk_freq.def_val/self.gui_m_div.def_val),
                                                                       editopt=0,
                                                                       hideopt=0,
                                                                       atrname='gui_phasedet_freq')

        # Enable Reference Clock Monitor
        self.gui_en_refclk_mon                              = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_refclk_mon')

        # Reference Clock Monitor frequency
        self.gui_refclk_mon_freq                            = gui_attr(options=[('3.2 MHz','3P2'), ('1.0 MHz','1P0')],
                                                                       def_val='3P2',
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_refclk_mon_freq')

        # ----------------------
        # Feedback Clock
        # ----------------------

        # Feedback mode
        self.gui_fbk_mode                                   = gui_attr(options=['CLKOP' ,
                                                                                'CLKOS' ,
                                                                                'CLKOS2',
                                                                                'CLKOS3',
                                                                                'CLKOS4',
                                                                                'CLKOS5',
                                                                                'INTCLKOP' ,
                                                                                'INTCLKOS' ,
                                                                                'INTCLKOS2',
                                                                                'INTCLKOS3',
                                                                                'INTCLKOS4',
                                                                                'INTCLKOS5'],
                                                                       def_val='INTCLKOP',
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       hidedsp=1,
                                                                       atrname='gui_fbk_mode')

        # Actual Feedback divider - to be recalculated later
        self.gui_n_div                                      = gui_attr(options=(self.PARAM_RANGE['N_DIV_I']['MIN'],
                                                                                self.PARAM_RANGE['N_DIV_I']['MAX']),
                                                                       def_val=self.PARAM_RANGE['N_DIV_I']['MIN'],
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_n_div')
        # Fractional Feedback divider
        self.gui_frac_n_div                                 = gui_attr(options=(self.PARAM_RANGE['FRAC_N']['MIN'],
                                                                                self.PARAM_RANGE['FRAC_N']['MAX']),
                                                                       def_val=self.PARAM_RANGE['FRAC_N']['MIN'],
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       hidedsp=1,
                                                                       atrname='gui_frac_n_div')

        # ----------------------
        # Spread Spectrum Clock
        # ----------------------

        # Spread Spectrum Profile
        self.gui_ssc_profile                                = gui_attr(options=[('Center Spread','CENTER'),('Down Spread','DOWN')],
                                                                       def_val='DOWN',
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_ssc_profile')

        # Spread Spectrum Modulation Depth
        self.gui_ssc_mod_depth                              = gui_attr(options=[0.25*step for step in range(1,9)],
                                                                       def_val=1.00,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_ssc_mod_depth')

        # Spread Spectrum Modulation Frequency
        self.gui_ssc_mod_freq                               = gui_attr(options=(round(100/4.095,2),200),
                                                                       def_val=100.0,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_ssc_mod_freq')


        # ----------------------
        # Clock Outputs
        # ----------------------

        # Generate attribute array for each output clock
        self.clk_idx                                        = {'CLKOP':0,'CLKOS':1,'CLKOS2':2,'CLKOS3':3,'CLKOS4':4,'CLKOS5':5}
        self.names_intclk_o                                 = dict([('INT'+ck,ck) for ck in self.clk_idx])
        self.STATIC_PHASE_SHIFT                             = [0,45,90,135,180,225,270,315]

        self.all_clkout_dis_or_byp                          = 0
        self.gui_clkout                                     = {}
        for ck in self.clk_idx:
            # initialize clock array
            self.gui_clkout[ck]                             = {}

            # Enable Clock
            self.gui_clkout[ck]['EN']                       = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=(1 if(ck == 'CLKOP') else 0),
                                                                       editopt=(0 if(ck == 'CLKOP') else 1),
                                                                       hideopt=(1 if(ck == 'CLKOP') else 0),
                                                                       atrname='gui_'+ck+'_en')

            # Bypass Clock
            self.gui_clkout[ck]['BYP']                      = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=(1 if(ck == 'CLKOP') else 0),
                                                                       hideopt=(0 if(ck == 'CLKOP') else 1),
                                                                       atrname='gui_'+ck+'_byp')

            # Clock Frequency
            self.gui_clkout[ck]['FREQ']                     = gui_attr(options=((self.PARAM_RANGE['FOUT_I']['MIN'], \
                                                                                 self.PARAM_RANGE['FOUT_I']['MAX']) if(ck == 'CLKOP') \
                                                                                else (self.PARAM_RANGE['FOUT_F']['MIN'], \
                                                                                      self.PARAM_RANGE['FOUT_F']['MAX'])),
                                                                       def_val=100.0,
                                                                       editopt=(1 if(ck == 'CLKOP') else 0),
                                                                       hideopt=(0 if(ck == 'CLKOP') else 1),
                                                                       hidedsp=1,
                                                                       atrname='gui_'+ck+'_freq')

            # Clock Divider
            self.gui_clkout[ck]['DIV']                      = gui_attr(options=(self.PARAM_RANGE['O_DIV']['MIN'],
                                                                                self.PARAM_RANGE['O_DIV']['MAX']),
                                                                       def_val=8,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       hidedsp=(0 if(ck == 'CLKOP') else 1),
                                                                       atrname='gui_'+ck+'_div')

            # Clock Phase
            self.gui_clkout[ck]['PHASE']                    = gui_attr(options=self.STATIC_PHASE_SHIFT,
                                                                       def_val=0,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_'+ck+'_phase')

            # Clock Tolerance
            self.gui_clkout[ck]['TOL']                      = gui_attr(options=[0.0, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0],
                                                                       def_val=0.0,
                                                                       editopt=(1 if(ck == 'CLKOP') else 0),
                                                                       hideopt=(0 if(ck == 'CLKOP') else 1),
                                                                       atrname='gui_'+ck+'_tol')

            # Clock difference in PPM (desired vs actual)
            self.gui_clkout[ck]['PPM']                      = gui_attr(options=(0,1000000.0),
                                                                       def_val=0.0,
                                                                       editopt=0,
                                                                       hideopt=(0 if(ck == 'CLKOP') else 1),
                                                                       atrname='gui_'+ck+'_ppm')

            # Add Clock Enable Port
            self.gui_clkout[ck]['CLKEN']                    = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_'+ck+'_clken')

            if(ck == 'CLKOP' or ck == 'CLKOS'):
                # Enable Clock Trim
                self.gui_clkout[ck]['TRIM_EN']              = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=(1 if(ck == 'CLKOP') else 0),
                                                                       hideopt=(0 if(ck == 'CLKOP') else 1),
                                                                       atrname='gui_'+ck+'_trim_en')

                # Clock Trim Mode
                self.gui_clkout[ck]['TRIM_MODE']            = gui_attr(options=['Rising', 'Falling'],
                                                                       def_val='Falling',
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_'+ck+'_trim_mode')

                # Clock Trim Delay Multiplier
                self.gui_clkout[ck]['TRIM_MULT']            = gui_attr(options=[('0', '000'), ('1', '001'), ('2', '010'), ('4', '100')],
                                                                       def_val='000',
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_'+ck+'_trim_mult')

        # ----------------------
        # Optional Ports
        # ----------------------

        # PLL RefClk from IO Pin
        self.gui_en_refclk_pin                              = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_refclk_pin')

        # PLL RefClk IO Type
        self.gui_refclk_io_type                             = gui_attr(options=['LVDS', 'SUBLVDS', 'SLVS', 'HSTL15_I', 'HSTL15D_I',
                                                                                'LVTTL33', 'LVCMOS33', 'LVCMOS25', 'LVCMOS18',
                                                                                'LVCMOS18H', 'HSTL15D_I', 'LVCMOS15', 'LVCMOS15H', 'LVCMOS12',
                                                                                'LVCMOS12H', 'LVCMOS10H', 'LVCMOS10', 'LVCMOS10R'],
                                                                       def_val='LVDS',
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_refclk_io_type')

        # Enable Dynamic Phase Ports
        self.gui_en_dyn_phase                               = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_dyn_phase')

        # Enable PLL Reset Port
        self.gui_en_pll_reset                               = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=1,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_pll_reset')

        # Enable PLL Lock Port
        self.gui_en_pll_lock                                = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=1,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_pll_lock')

        # PLL Lock Sticky
        self.gui_pll_lock_sticky                            = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_pll_lock_sticky')

        # Register interface
        self.gui_reg_interface                              = gui_attr(options=['None', 'APB', 'LMMI'],
                                                                       def_val='None',
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_reg_interface')

        # CSR Enable
        self.gui_en_csr                                     = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=0,
                                                                       hideopt=1,
                                                                       atrname='gui_en_csr')

        # Enable Legacy Mode
        self.gui_en_legacy                                  = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_legacy')

        # Enable Powerdown Port
        self.gui_en_powerdown                               = gui_attr(options=[('False', 0), ('True', 1)],
                                                                       def_val=0,
                                                                       editopt=1,
                                                                       hideopt=0,
                                                                       atrname='gui_en_powerdown')

        # -------------------------------------------------------------------------------------------------------------
        # Parameters needed in calculation of analog setting optimization
        # -------------------------------------------------------------------------------------------------------------
        # Deg-Rad conversion
        self.d180_overPI                                    = 57.295779513082320876798154814105

        # Percent error for rounding off if Tolerance is zero
        self.TOL_NEAR_ZERO                                  = 1e-6

        (self.s_list,self.func_coef)                        = self.init_analog_params()

        self.analog_param                                   = {'ipp_ctrl'    :'0b'+bin(4)[2:].rjust(4,'0'),
                                                               'bw_ctrl_bias':'0b'+bin(15)[2:].rjust(4,'0'),
                                                               'ipp_sel'     :'0b'+bin(15)[2:].rjust(4,'0'),
                                                               'ipi_cmp'     :'0b'+bin(4)[2:].rjust(4,'0'),
                                                               'v2i_pp_res'  :str(9.0).replace('.0','K'),
                                                               'cset'        :str(24)+'P',
                                                               'cripple'     :str(3)+'P'
                                                               }


        div_ratio                                           = self.gui_m_div.def_val/(self.gui_n_div.def_val*self.gui_clkout['CLKOP']['DIV'].def_val)
        self.ref_count                                      = self.get_ref_count_value(div_ratio)

        # List of valid combination of dividers
        self.mno_dict                                       = {}
        self.n_div_list                                     = []
        self.m_div_list                                     = []
        self.o_div_dict                                     = {}
        self.invalid_mno                                    = 0

        self.rtl_params                                     = self.set_rtl_params()
    # end def __init__

    def init_analog_params(self,tol=1e-4):
        log10                                               = self.log10
        abs                                                 = self.abs

        PI                                                  = 3.1415926535897932384626433832795
        PI_2                                                = 6.283185307179586476925286766559
        ln10                                                = 2.3025850929940456840179914546844

        # Analog Parameters - from LMMI registers
        IPP_CTRL                                            = tuple(range(1,4+1))
        IPP_CTRL_MULT                                       = 1e-6
        BW_CTL_BIAS                                         = tuple(range(1,15+1))
        IPP_SEL                                             = tuple(range(1,4+1))
        IPI_CMP                                             = tuple(range(1,15+1))
        IPI_CMP_MULT                                        = 0.5e-6
        CSET                                                = tuple(range(2,17+1))
        CSET_MULT                                           = 4e-12
        CRIPPLE                                             = tuple([1+i*2 for i in range(0,7+1)])
        CRIPPLE_MULT                                        = 1e-12
        V2I_PP_RES                                          = (10.7, 10.3, 10.0, 9.7, 9.3, 9.0)
        V2I_PP_RES_ACTUAL                                   = {10.7:10.644681, 10.3:10.317022,
                                                               10.0:9.98936, 9.7:9.661701, 9.3:9.334041, 9.0:9.006382}
        V2I_PP_RES_MULT                                     = 1e3


        # Get list of valid values for the condition ip/i2 == 50
        self.valid_ip_i2         = {}
        uniqe_ip                 = set()
        ipp_sel_actual_value_map = {1:1,2:3,3:7,4:15}
        # Total valid_ip_i2 is 8 if ip/i2==50, 303 if ip/i2>=50
        for ipp_ctrl in IPP_CTRL:
            for bw_ctl_bias in BW_CTL_BIAS:
                for ipp_sel in IPP_SEL:
                    ip = (5.0/3)*ipp_ctrl*bw_ctl_bias*ipp_sel*IPP_CTRL_MULT
                    if(ip not in uniqe_ip):
                        uniqe_ip.add(ip)
                        for ipi_cmp in IPI_CMP:
                            i2 = ipi_cmp*IPI_CMP_MULT
                            #if(ip/i2 == 50):
                            if(abs(ip/i2 - 50) <= tol):
                                # actual value of ipp_ctrl = 0b01??
                                self.valid_ip_i2[(('ipp_ctrl'    ,(4+ipp_ctrl-1)),
                                                  ('bw_ctrl_bias',bw_ctl_bias),
                                                  ('ipp_sel'     ,ipp_sel_actual_value_map[ipp_sel]),
                                                  ('ipi_cmp'     ,ipi_cmp))] = {'ip':ip,'i2':i2}

        g3                                                  = 0.2952e-3
        ki                                                  = 508e9 # (MHz/A)
        c2_list                                             = [c2*CSET_MULT for c2 in CSET]
        cs_list                                             = [cs*CRIPPLE_MULT for cs in CRIPPLE]
        #r_list                                              = [r*V2I_PP_RES_MULT for r in V2I_PP_RES]
        k1                                                  = 6
        r1                                                  = 9.8e6
        c3                                                  = 20e-12
        k3                                                  = 100

        func_coef = {}
        #       AG+A(Bs+1)        E         (ABF+EC)s^2 + (A(F(G+1)+B) + ED)s + A(G+1)
        #lg3 = ------------ + ---------- = --------------------------------------------
        #       ns^2(Cs+D)     ns(Fs+1)            ns^2(CFs^2 + (DF+C)s + D)

        #A = i2*g3*ki
        #B = r1*c3
        #C = _B*c2
        #D = c2+c3
        #E = io*ki*k1
        #F = r*cs
        #G = k3

        #_C1 = ABF+EC
        #_C2 = A(F(G+1)+B)+ED
        #_C3 = A(G+1)
        #_C4 = CF
        #_C5 = DF+C
        #_C6 = D

        _B = r1*c3
        _G = k3
        for c2 in c2_list: # 16 loops
            _C = _B*c2
            _D  = c2+c3
            for r in V2I_PP_RES_ACTUAL: # 8 loops
                for cs in cs_list: # 8 loops
                    _F = V2I_PP_RES_ACTUAL[r]*V2I_PP_RES_MULT*cs
                    for i_params in self.valid_ip_i2: # 8 loops, (303 if ip/12 >= 50)
                        io = self.valid_ip_i2[i_params]['ip']
                        i2 = self.valid_ip_i2[i_params]['i2']
                        _A    = i2*g3*ki
                        _E    = io*ki*k1

                        _C1 = _A*_B*_F + _E*_C
                        _C2 = _A*(_F*(_G + 1) + _B) + _E*_D
                        _C3 = _A*(_G+1)
                        _C4 = _C*_F
                        _C5 = _D*_F + _C
                        _C6 = _D

                        func_coef[(i_params + (
                                   ('cset'      ,(int(c2/CSET_MULT)*4)),
                                   ('v2i_pp_res',r),
                                   ('cripple'   ,int(cs/CRIPPLE_MULT))))] = {'C1':_C1,
                                                                             'C2':_C2,
                                                                             'C3':_C3,
                                                                             'C4':_C4,
                                                                             'C5':_C5,
                                                                             'C6':_C6}

        # generate f values from 1 KHz to 1 GHz
        resol               = 0.02
        f_np                = self.np.exp(self.np.arange(3, 9+resol, resol) * self.np.log(10))
        s_np                = 1j * PI_2 * f_np
        s2_np               = s_np ** 2
        s_list              = [f_np,s_np,s2_np]


        #s_list              = {}
        #step                = 2
        #k_idx               = 0
        #for i in range(1,4): # 3 loops
        #    step_factor     = 10**i
        #    start           = int(round(step_factor*log10(1e5),i))
        #    end             = int(round(step_factor*log10(1e9),i))
        #    # Sweep frequency from 1MHz to 1GHz
        #    for k in range(start,(end+step),step): # max 11 loops
        #        f           = self.exp(k*ln10/step_factor)
        #        w           = PI_2 * f
        #        s           = 1j * w
        #        s_2         = -w**2
        #        k_idx       = k_idx + 1
        #        s_list[k]   = (f,s,s_2,k_idx)
        #s_list_keys = list(s_list.keys())
        #s_list_keys.sort()

        return (s_list,func_coef)

    # end def init_analog_params

    def print_attr(self,debug=0):
        if(debug):
            print("\n")
            self.gui_config_mode.print_attr_values()
            self.gui_optim_prio.print_attr_values()
            self.gui_en_frac_n.print_attr_values()
            self.gui_en_ssc.print_attr_values()
            self.gui_en_usr_fbk.print_attr_values()
            self.gui_en_pmu_wait_lock.print_attr_values()
            self.gui_en_int_fbkdel_sel.print_attr_values()
            self.gui_vco_freq.print_attr_values()
            self.gui_refclk_freq.print_attr_values()
            self.gui_m_div.print_attr_values()
            self.gui_phasedet_freq.print_attr_values()
            self.gui_en_refclk_mon.print_attr_values()
            self.gui_refclk_mon_freq.print_attr_values()
            self.gui_fbk_mode.print_attr_values()
            self.gui_n_div.print_attr_values()
            self.gui_frac_n_div.print_attr_values()
            self.gui_ssc_profile.print_attr_values()
            self.gui_ssc_mod_depth.print_attr_values()
            self.gui_ssc_mod_freq.print_attr_values()
            self.gui_clkout['CLKOP']['EN'].print_attr_values()
            self.gui_clkout['CLKOP']['BYP'].print_attr_values()
            self.gui_clkout['CLKOP']['FREQ'].print_attr_values()
            self.gui_clkout['CLKOP']['DIV'].print_attr_values()
            self.gui_clkout['CLKOP']['PHASE'].print_attr_values()
            self.gui_clkout['CLKOP']['TOL'].print_attr_values()
            self.gui_clkout['CLKOP']['PPM'].print_attr_values()
            self.gui_clkout['CLKOP']['CLKEN'].print_attr_values()
            self.gui_clkout['CLKOP']['TRIM_EN'].print_attr_values()
            self.gui_clkout['CLKOP']['TRIM_MODE'].print_attr_values()
            self.gui_clkout['CLKOP']['TRIM_MULT'].print_attr_values()
            self.gui_clkout['CLKOS']['EN'].print_attr_values()
            self.gui_clkout['CLKOS']['BYP'].print_attr_values()
            print("\n")
        return "print_attr: done"

    def set_attr(self,gui_config_mode, gui_optim_prio, gui_en_frac_n, gui_en_ssc,
                      gui_en_usr_fbk, gui_en_pmu_wait_lock, gui_en_int_fbkdel_sel,
                      gui_refclk_freq, gui_m_div, gui_en_refclk_mon,
                      gui_refclk_mon_freq, gui_fbk_mode, gui_n_div,
                      gui_frac_n_div, gui_ssc_profile, gui_ssc_mod_depth,
                      gui_ssc_mod_freq,
                      gui_en_refclk_pin, gui_refclk_io_type, gui_en_dyn_phase,
                      gui_en_pll_reset, gui_en_pll_lock, gui_pll_lock_sticky,
                      gui_reg_interface, gui_en_csr, gui_en_legacy, gui_en_powerdown,
                      gui_clkout):

        abs                                                 = self.abs
        # -------------------------------------------------------------------------------------
        # Calculate Next Value of Active GUI Attributes
        # -------------------------------------------------------------------------------------

        # Reset bypass_bw_factor if User changed parameters
        if(self.bypass_bw_factor):
            if(self.changed_value(self.gui_config_mode.usr_val , gui_config_mode ) or
               self.changed_value(self.gui_en_usr_fbk.usr_val  , gui_en_usr_fbk  ) or
               self.changed_value(self.gui_fbk_mode.usr_val    , gui_fbk_mode    ) or
               self.changed_value(self.gui_refclk_freq.usr_val , gui_refclk_freq ) or
               self.changed_value(self.gui_en_frac_n.usr_val   , gui_en_frac_n   ) or
               self.changed_value(self.gui_en_ssc.usr_val      , gui_en_ssc      ) or
               self.changed_value(self.gui_m_div.usr_val       , gui_m_div       ) or
               self.changed_value(self.gui_n_div.usr_val       , gui_n_div       ) or
               self.changed_value(self.gui_frac_n_div.usr_val  , gui_frac_n_div  )
              ):
                self.bypass_bw_factor                       = 0

        self.invalid_mno                                    = 0
        m_range                                             = (self.PARAM_RANGE['M_DIV']['MIN'],
                                                               self.PARAM_RANGE['M_DIV']['MAX'])
        n_range                                             = (self.PARAM_RANGE['N_DIV_I']['MIN'],
                                                               self.PARAM_RANGE['N_DIV_I']['MAX'])
        fn_range                                            = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MAX'])

        if(check_is_jp_device()):
            m_div = 2 if(gui_refclk_freq > self.PARAM_RANGE['FPFD_JP']['MAX']) else 1
        else:
            m_div = 2 if(gui_refclk_freq > self.PARAM_RANGE['FPFD_I']['MAX']) else 1

        n_div                                               = 1

        fbk_clk_opts                                        = self.gen_fb_clk_opts(gui_en_frac_n,gui_en_ssc,gui_en_usr_fbk,gui_clkout)
        set_fbk_clk                                         = 'INTCLKOP' if(gui_en_frac_n or gui_en_ssc or gui_en_usr_fbk) else gui_fbk_mode
        clk_fbk_name                                        = set_fbk_clk.replace('INT','')

        o_div                                               = {}
        o_range                                             = {}
        for ck in gui_clkout:
            # Reset bypass_bw_factor if User changed parameters
            if(self.bypass_bw_factor):
                if(self.changed_value(self.gui_clkout[ck]['EN'].usr_val   , gui_clkout[ck]['EN']  ) or
                   self.changed_value(self.gui_clkout[ck]['BYP'].usr_val  , gui_clkout[ck]['BYP'] ) or
                   self.changed_value(self.gui_clkout[ck]['FREQ'].usr_val , gui_clkout[ck]['FREQ']) or
                   self.changed_value(self.gui_clkout[ck]['DIV'].usr_val  , gui_clkout[ck]['DIV'] )
                  ):
                    self.bypass_bw_factor                   = 0

            o_div[ck]                                       = self.gui_clkout[ck]['DIV'].def_val
            o_range[ck]                                     = (self.PARAM_RANGE['O_DIV']['MIN'],
                                                               self.PARAM_RANGE['O_DIV']['MAX'])
            if(ck == clk_fbk_name):
                if(ck == 'CLKOP'):
                    if(set_fbk_clk == 'CLKOP'):
                        gui_clkout[ck]['BYP']               = 0
                else:
                    gui_clkout[ck]['BYP']                   = 0
                gui_clkout[ck]['EN']                        = 1

            # no bypass in FracN or SSC
            if(gui_en_frac_n or gui_en_ssc):
                gui_clkout[ck]['BYP']                       = 0
            if(gui_en_usr_fbk and ck == 'CLKOP'):
                gui_clkout[ck]['BYP']                       = 0

        self.all_clkout_dis_or_byp                          = self.all_clkout_disabled_or_bypassed(gui_clkout)

        if(gui_config_mode == 'FREQUENCY'):
            # at least 1 enabled output clock and not bypassed
            if(not self.all_clkout_dis_or_byp):
                Fout_d                                      = {}
                Tol_d                                       = {}
                for ck in gui_clkout:
                    if(gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']):
                        Fout_d[ck] = gui_clkout[ck]['FREQ']
                        Tol_d[ck]  = gui_clkout[ck]['TOL'] if(gui_clkout[ck]['TOL'] > 0) else self.TOL_NEAR_ZERO

                # Search valid combination of dividers
                if(gui_en_frac_n or gui_en_ssc):
                    (self.mno_dict,
                     self.n_div_list,
                     self.m_div_list,
                     self.o_div_dict) = self.calc_fracN_divider(gui_refclk_freq,
                                                                Fout_d,
                                                                Tol_d,
                                                                gui_en_frac_n,
                                                                gui_en_ssc)
                else:
                    (self.mno_dict,
                     self.n_div_list,
                     self.m_div_list,
                     self.o_div_dict) = self.calc_int_dividers(gui_refclk_freq,
                                                               clk_fbk_name,
                                                               Fout_d,
                                                               Tol_d)
                if(len(self.mno_dict)):
                    self.invalid_mno = 0
                    # update valid range of ref clock divider
                    m_range = (min(self.m_div_list),max(self.m_div_list))
                    m_div   = m_range[0]

                    # update valid range for feedback divider
                    n_range = (int(min(self.n_div_list)),int(max(self.n_div_list)))
                    n_div   = min(list(self.mno_dict[m_div].keys()))

                    # update output dividers
                    o_div   = {}
                    o_range = {}
                    for ck in gui_clkout:
                        if(ck in Fout_d):
                            o_div[ck]   = min(self.mno_dict[m_div][n_div][ck])
                            o_range[ck] = (min(self.o_div_dict[ck]),max(self.o_div_dict[ck]))
                        else:
                            o_div[ck]   = self.gui_clkout[ck]['DIV'].def_val
                            o_range[ck] = (self.PARAM_RANGE['O_DIV']['MIN'],
                                           self.PARAM_RANGE['O_DIV']['MAX'])

                else: # empty mno_dict
                    self.invalid_mno = 1

        else: # gui_config_mode == 'DIVIDER'
            m_range                                         = self.get_refck_div_range(gui_refclk_freq,
                                                                                       gui_en_frac_n,gui_en_ssc)
            n_range                                         = self.get_fbk_div_range(gui_en_frac_n,gui_en_ssc,
                                                                                     gui_config_mode,
                                                                                     (1.0*gui_refclk_freq/gui_m_div))
            m_div                                           = gui_m_div
            if(gui_en_frac_n):
                n_div                                       = gui_n_div + (1.0*gui_frac_n_div/self.FRAC_N_MAX1)
            else:
                n_div                                       = gui_n_div

            o_div                                           = {}
            o_range                                         = {}
            for ck in gui_clkout:
                o_range[ck]                                 = (self.PARAM_RANGE['O_DIV']['MIN'],
                                                               self.PARAM_RANGE['O_DIV']['MAX'])
                if(gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']):
                    o_div[ck]                               = gui_clkout[ck]['DIV']
                else:
                    o_div[ck]                               = self.gui_clkout[ck]['DIV'].def_val

            self.mno_dict                                   = {}
            self.mno_dict[m_div]                            = {}
            self.mno_dict[m_div][n_div]                     = {}

            freq_phasedet                                   = gui_refclk_freq/m_div

            if(gui_en_frac_n or gui_en_ssc):
                # list all enabled clock outputs
                list_clk_o                                  = [key for key in gui_clkout \
                                                                       if(gui_clkout[key]['EN'] and not gui_clkout[key]['BYP'])]
                # calculate actual VCO frequency
                vco_freq                                    = freq_phasedet*n_div

                # calculate range of Fractional N
                if(gui_en_frac_n):
                    if(gui_n_div == n_range[0]): # minimum
                        fvco = freq_phasedet*gui_n_div
                        if(fvco < self.PARAM_RANGE['FVCO']['MIN']):
                            dec_n                           = ((self.PARAM_RANGE['FVCO']['MIN']/freq_phasedet) % 1)*self.FRAC_N_MAX1
                            frac_n                          = int(dec_n)+1 if(dec_n % 1 > 0 and dec_n < self.PARAM_RANGE['FRAC_N']['MAX']) else int(dec_n)
                            fn_range                        = (frac_n,self.PARAM_RANGE['FRAC_N']['MAX'])
                        elif(fvco == self.PARAM_RANGE['FVCO']['MAX']):
                            fn_range                        = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MIN'])
                        else:
                            fn_range                        = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MAX'])
                    elif(gui_n_div == n_range[1]): # maximum
                        fvco                                = freq_phasedet*(gui_n_div+(1.0*self.PARAM_RANGE['FRAC_N']['MAX']/self.FRAC_N_MAX1))
                        if(fvco > self.PARAM_RANGE['FVCO']['MAX']):
                            frac_n                          = int(((self.PARAM_RANGE['FVCO']['MAX']/freq_phasedet) % 1)*self.FRAC_N_MAX1)
                            fn_range                        = (self.PARAM_RANGE['FRAC_N']['MIN'],frac_n)
                        else:
                            fn_range                        = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MAX'])
                    else: # inside n_range
                        fn_range                            = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MAX'])
                else:
                    fn_range                                = (self.PARAM_RANGE['FRAC_N']['MIN'],
                                                               self.PARAM_RANGE['FRAC_N']['MAX'])

            else: # integer N divider and not ssc_en
                # list all enabled clock outputs excluding the feedback
                list_clk_o                                  = [key for key in gui_clkout if(key != clk_fbk_name and \
                                                                                            gui_clkout[key]['EN'] and \
                                                                                            not gui_clkout[key]['BYP'])]
                # calculate actual VCO frequency
                vco_freq                                    = o_div[clk_fbk_name]*freq_phasedet*n_div

                if(gui_clkout[clk_fbk_name]['EN'] and not gui_clkout[clk_fbk_name]['BYP']):
                    # calculate range of ouput divider used as feedback
                    min_div_o                               = int(self.PARAM_RANGE['FVCO']['MIN']/(freq_phasedet*n_div))
                    if(self.PARAM_RANGE['FVCO']['MIN'] % (freq_phasedet*n_div) > 0):
                        min_div_o                           = min_div_o + 1

                    min_vco                                 = min_div_o*freq_phasedet*n_div
                    if(min_div_o > self.PARAM_RANGE['O_DIV']['MAX']):
                        min_div_o                           = self.PARAM_RANGE['O_DIV']['MAX']

                    max_div_o                               = int(self.PARAM_RANGE['FVCO']['MAX']/(freq_phasedet*n_div))
                    if(max_div_o > self.PARAM_RANGE['O_DIV']['MAX']):
                        max_div_o                           = self.PARAM_RANGE['O_DIV']['MAX']

                    o_range[clk_fbk_name]                   = (min_div_o,max_div_o)

                    self.mno_dict[m_div][n_div][clk_fbk_name]= [o_div[clk_fbk_name]]

            # calculate/update range of ouput divider
            for ck in list_clk_o:
                min_div_o                                   = int(vco_freq/self.PARAM_RANGE['FOUT_F']['MAX'])
                if(min_div_o < self.PARAM_RANGE['O_DIV']['MIN']):
                    min_div_o                               = self.PARAM_RANGE['O_DIV']['MIN']
                elif(vco_freq % self.PARAM_RANGE['FOUT_F']['MAX'] > 0):
                    min_div_o                               = min_div_o + 1

                max_div_o                                   = int(vco_freq/self.PARAM_RANGE['FOUT_F']['MIN'])
                if(max_div_o > self.PARAM_RANGE['O_DIV']['MAX']):
                    max_div_o                               = self.PARAM_RANGE['O_DIV']['MAX']

                o_range[ck]                                 = (min_div_o,max_div_o)

                self.mno_dict[m_div][n_div][ck]             = [o_div[ck]]


        # get fractional part of n_div
        frac_n_div                                          = round((n_div % 1) * self.FRAC_N_MAX1) if(gui_en_frac_n) else 0

        # calculate actual VCO frequency
        if(not self.all_clkout_dis_or_byp):
            if(gui_en_frac_n or gui_en_ssc):
                vco_freq                                    = (n_div*gui_refclk_freq)/m_div
            else:
                vco_freq                                    = (o_div[clk_fbk_name]*n_div*gui_refclk_freq)/m_div
        else:
            vco_freq                                        = self.gui_vco_freq.def_val

        # calculate actual output frequency
        clk_o_freq = {}
        for ck in gui_clkout:
            if(gui_clkout[ck]['EN']):
                if(gui_clkout[ck]['BYP']):
                    clk_o_freq[ck]                          = gui_refclk_freq
                else:
                    clk_o_freq[ck]                          = vco_freq/o_div[ck]
            else:
                clk_o_freq[ck]                              = self.gui_clkout[ck]['FREQ'].def_val

        # -------------------------------------------------------------------------------------
        # Set Next Value of GUI Attributes
        # -------------------------------------------------------------------------------------
        # ----------------------
        # General
        # ----------------------

        # Configuration Mode
        self.gui_config_mode.usr_val                        = gui_config_mode

        # Parameter Optimization Target
        self.gui_optim_prio.usr_val                         = gui_optim_prio

        # Enable Fractional-N Divider
        self.gui_en_frac_n.usr_val                          = gui_en_frac_n

        # Enable Spread Spectrum Clock
        self.gui_en_ssc.usr_val                             = gui_en_ssc

        # Enable User Feedback clock
        self.gui_en_usr_fbk.editopt                         = not (gui_en_frac_n or gui_en_ssc)
        self.gui_en_usr_fbk.hideopt                         = not self.gui_en_usr_fbk.editopt
        self.gui_en_usr_fbk.usr_val                         = gui_en_usr_fbk
        self.gui_en_usr_fbk.cal_val                         = bool(self.gui_en_usr_fbk.def_val)

        # Enable PMU wait for PLL Lock
        self.gui_en_pmu_wait_lock.usr_val                   = gui_en_pmu_wait_lock

        # Enable Internal Path Swithing
        self.gui_en_int_fbkdel_sel.usr_val                  = gui_en_int_fbkdel_sel

        # ----------------------
        # Reference Clock
        # ----------------------

        # Reference Clock Frequency
        self.gui_refclk_freq.usr_val                        = gui_refclk_freq

        # Reference clock divider
        self.gui_m_div.editopt                              = (gui_config_mode == 'DIVIDER'  )
        self.gui_m_div.hideopt                              = not self.gui_m_div.editopt
        self.gui_m_div.hidedsp                              = not self.gui_m_div.hideopt
        self.gui_m_div.options                              = m_range if(not self.gui_m_div.hideopt) \
                                                              else (self.PARAM_RANGE['M_DIV']['MIN'],\
                                                                    self.PARAM_RANGE['M_DIV']['MAX']) # re-calculate
        self.gui_m_div.usr_val                              = gui_m_div
        self.gui_m_div.cal_val                              = m_div # re-calculate

        # Phase detector frequency
        if(check_is_jp_device()):
            self.gui_phasedet_freq.options                      = (self.PARAM_RANGE['FPFD_JP']['MIN'], \
                                                               self.PARAM_RANGE['FPFD_JP']['MAX'])
        else:
            self.gui_phasedet_freq.options                      = (self.PARAM_RANGE['FPFD_F']['MIN'], \
                                                               self.PARAM_RANGE['FPFD_F']['MAX']) if(gui_en_frac_n or gui_en_ssc) \
                                                              else (self.PARAM_RANGE['FPFD_I']['MIN'], \
                                                                    self.PARAM_RANGE['FPFD_I']['MAX'])

        self.gui_phasedet_freq.cal_val                      = gui_refclk_freq/m_div

        # Actual VCO frequency
        self.gui_vco_freq.cal_val                           = vco_freq if(vco_freq >= self.PARAM_RANGE['FVCO']['MIN'] and \
                                                                          vco_freq <= self.PARAM_RANGE['FVCO']['MAX']) else \
                                                              self.PARAM_RANGE['FVCO']['MIN'] # re-calculate

        # Enable Reference Clock Monitor
        self.gui_en_refclk_mon.usr_val                      = gui_en_refclk_mon
        self.gui_en_refclk_mon.editopt                      = not check_is_jp_device()

        # Reference Clock Monitor frequency
        self.gui_refclk_mon_freq.editopt                    = gui_en_refclk_mon
        self.gui_refclk_mon_freq.hideopt                    = not self.gui_refclk_mon_freq.editopt
        self.gui_refclk_mon_freq.usr_val                    = gui_refclk_mon_freq
        self.gui_refclk_mon_freq.cal_val                    = self.gui_refclk_mon_freq.def_val

        # ----------------------
        # Feedback Clock
        # ----------------------

        # Feedback mode
        self.gui_fbk_mode.editopt                           = not (gui_en_frac_n or gui_en_ssc or gui_en_usr_fbk)
        self.gui_fbk_mode.hideopt                           = not self.gui_fbk_mode.editopt
        self.gui_fbk_mode.hidedsp                           = not self.gui_fbk_mode.hideopt
        self.gui_fbk_mode.usr_val                           = gui_fbk_mode
        self.gui_fbk_mode.cal_val                           = gui_fbk_mode if(self.gui_fbk_mode.editopt) else 'INTCLKOP' # re-calculate

        # Actual Feedback divider
        self.gui_n_div.editopt                              = (gui_config_mode == 'DIVIDER')
        self.gui_n_div.hideopt                              = not self.gui_n_div.editopt
        self.gui_n_div.hidedsp                              = not self.gui_n_div.hideopt or bool(self.all_clkout_dis_or_byp)
        self.gui_n_div.options                              = n_range if(not self.gui_n_div.hideopt) \
                                                              else (self.PARAM_RANGE['N_DIV_I']['MIN'], \
                                                                    self.PARAM_RANGE['N_DIV_I']['MAX']) # re-calculate
        self.gui_n_div.usr_val                              = gui_n_div
        self.gui_n_div.cal_val                              = n_div # re-calculate

        # Fractional Feedback divider
        self.gui_frac_n_div.editopt                         = (gui_config_mode == 'DIVIDER' and gui_en_frac_n)
        self.gui_frac_n_div.hideopt                         = not self.gui_frac_n_div.editopt
        self.gui_frac_n_div.hidedsp                         = not gui_en_frac_n or (gui_config_mode == 'DIVIDER')
        self.gui_frac_n_div.options                         = fn_range if(not self.gui_frac_n_div.hideopt) \
                                                              else (self.PARAM_RANGE['FRAC_N']['MIN'], \
                                                                    self.PARAM_RANGE['FRAC_N']['MAX']) # re-calculate
        self.gui_frac_n_div.usr_val                         = gui_frac_n_div
        self.gui_frac_n_div.cal_val                         = frac_n_div # re-calculate

        # ----------------------
        # Spread Spectrum Clock
        # ----------------------

        # Spread Spectrum Profile
        self.gui_ssc_profile.editopt                        = gui_en_ssc
        self.gui_ssc_profile.hideopt                        = not self.gui_ssc_profile.editopt
        self.gui_ssc_profile.usr_val                        = gui_ssc_profile
        self.gui_ssc_profile.cal_val                        = self.gui_ssc_profile.def_val

        # Spread Spectrum Modulation Depth
        self.gui_ssc_mod_depth.editopt                      = gui_en_ssc
        self.gui_ssc_mod_depth.hideopt                      = not self.gui_ssc_mod_depth.editopt
        self.gui_ssc_mod_depth.usr_val                      = gui_ssc_mod_depth
        self.gui_ssc_mod_depth.cal_val                      = self.gui_ssc_mod_depth.def_val

        # Spread Spectrum Modulation Frequency
        self.gui_ssc_mod_freq.editopt                       = gui_en_ssc
        self.gui_ssc_mod_freq.hideopt                       = not self.gui_ssc_mod_freq.editopt
        self.gui_ssc_mod_freq.usr_val                       = gui_ssc_mod_freq
        self.gui_ssc_mod_freq.cal_val                       = self.gui_ssc_mod_freq.def_val

        # ----------------------
        # Clock Outputs
        # ----------------------

        for ck in self.gui_clkout:
            if(ck == 'CLKOP'):
                self.gui_clkout[ck]['BYP'].editopt          = not (gui_en_frac_n or gui_en_ssc or gui_en_usr_fbk or (set_fbk_clk == ck))
                self.gui_clkout[ck]['BYP'].hideopt          = not self.gui_clkout[ck]['BYP'].editopt
            else:
                # Enable Clock
                self.gui_clkout[ck]['EN'].editopt           = gui_clkout['CLKOP']['BYP'] or not (clk_fbk_name == ck)
                self.gui_clkout[ck]['EN'].hideopt           = not self.gui_clkout[ck]['EN'].editopt
                self.gui_clkout[ck]['EN'].usr_val           = gui_clkout[ck]['EN']
                self.gui_clkout[ck]['EN'].cal_val           = bool(self.gui_clkout[ck]['EN'].usr_val)

                # Bypass Clock
                self.gui_clkout[ck]['BYP'].editopt          = not (not gui_clkout[ck]['EN'] or gui_en_frac_n or gui_en_ssc)
                self.gui_clkout[ck]['BYP'].hideopt          = not self.gui_clkout[ck]['BYP'].editopt or \
                                                              (not gui_clkout['CLKOP']['BYP'] and (clk_fbk_name == ck))

            self.gui_clkout[ck]['BYP'].usr_val              = gui_clkout[ck]['BYP']
            self.gui_clkout[ck]['BYP'].cal_val              = bool(self.gui_clkout[ck]['BYP'].def_val)

            # Clock Frequency
            self.gui_clkout[ck]['FREQ'].editopt             = (gui_config_mode == 'FREQUENCY') and gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']
            self.gui_clkout[ck]['FREQ'].hideopt             = not self.gui_clkout[ck]['FREQ'].editopt
            self.gui_clkout[ck]['FREQ'].hidedsp             = not gui_clkout[ck]['EN'] or gui_clkout[ck]['BYP'] or \
                                                              ((gui_config_mode == 'FREQUENCY') and abs(gui_clkout[ck]['FREQ'] - clk_o_freq[ck]) <= self.TOL_NEAR_ZERO)
            self.gui_clkout[ck]['FREQ'].options             = self.get_clk_o_range((clk_fbk_name == ck and not(gui_en_frac_n or gui_en_ssc))) \
                                                              if(not self.gui_clkout[ck]['FREQ'].hideopt) \
                                                              else (self.PARAM_RANGE['FOUT_F']['MIN'], self.PARAM_RANGE['FOUT_F']['MAX']) # re-calculate
            self.gui_clkout[ck]['FREQ'].usr_val             = gui_clkout[ck]['FREQ']
            self.gui_clkout[ck]['FREQ'].cal_val             = clk_o_freq[ck] # re-calculate

            # Clock Divider
            self.gui_clkout[ck]['DIV'].editopt              = (gui_config_mode == 'DIVIDER') and gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']
            self.gui_clkout[ck]['DIV'].hideopt              = not self.gui_clkout[ck]['DIV'].editopt
            self.gui_clkout[ck]['DIV'].hidedsp              = not self.gui_clkout[ck]['DIV'].hideopt or not gui_clkout[ck]['EN'] or gui_clkout[ck]['BYP']
            self.gui_clkout[ck]['DIV'].options              = o_range[ck] if(not self.gui_clkout[ck]['DIV'].hideopt) \
                                                              else (self.PARAM_RANGE['O_DIV']['MIN'], self.PARAM_RANGE['O_DIV']['MAX']) # re-calculate
            self.gui_clkout[ck]['DIV'].usr_val              = gui_clkout[ck]['DIV']
            self.gui_clkout[ck]['DIV'].cal_val              = o_div[ck] # re-calculate

            # Clock Phase
            self.gui_clkout[ck]['PHASE'].editopt            = not (not gui_clkout[ck]['EN'] or gui_clkout[ck]['BYP'] or (clk_fbk_name == ck))
            self.gui_clkout[ck]['PHASE'].hideopt            = not self.gui_clkout[ck]['PHASE'].editopt
            self.gui_clkout[ck]['PHASE'].usr_val            = gui_clkout[ck]['PHASE']
            self.gui_clkout[ck]['PHASE'].cal_val            = self.gui_clkout[ck]['PHASE'].def_val

            # Clock Tolerance
            self.gui_clkout[ck]['TOL'].editopt              = (gui_config_mode == 'FREQUENCY') and gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']
            self.gui_clkout[ck]['TOL'].hideopt              = not self.gui_clkout[ck]['TOL'].editopt
            self.gui_clkout[ck]['TOL'].usr_val              = gui_clkout[ck]['TOL']
            self.gui_clkout[ck]['TOL'].cal_val              = self.gui_clkout[ck]['TOL'].def_val

            # Clock difference in PPM (desired vs actual)
            self.gui_clkout[ck]['PPM'].hideopt              = not gui_clkout[ck]['EN'] or gui_clkout[ck]['BYP'] or gui_config_mode == 'DIVIDER'
            self.gui_clkout[ck]['PPM'].cal_val              = self.calc_ppm(self.gui_clkout[ck]['FREQ'].usr_val,
                                                                            self.gui_clkout[ck]['FREQ'].cal_val)

            # Add Clock Enable Port
            self.gui_clkout[ck]['CLKEN'].editopt            = not (not gui_clkout[ck]['EN'] or gui_clkout[ck]['BYP'] or (clk_fbk_name == ck))
            self.gui_clkout[ck]['CLKEN'].hideopt            = not self.gui_clkout[ck]['CLKEN'].editopt
            self.gui_clkout[ck]['CLKEN'].usr_val            = gui_clkout[ck]['CLKEN']
            self.gui_clkout[ck]['CLKEN'].cal_val            = self.gui_clkout[ck]['CLKEN'].def_val

            if(ck == 'CLKOP' or ck == 'CLKOS'):
                # Enable Clock Trim
                self.gui_clkout[ck]['TRIM_EN'].editopt      = gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']
                self.gui_clkout[ck]['TRIM_EN'].hideopt      = not self.gui_clkout[ck]['TRIM_EN'].editopt
                self.gui_clkout[ck]['TRIM_EN'].usr_val      = gui_clkout[ck]['TRIM_EN']
                self.gui_clkout[ck]['TRIM_EN'].cal_val      = self.gui_clkout[ck]['TRIM_EN'].def_val

                # Clock Trim Mode
                self.gui_clkout[ck]['TRIM_MODE'].editopt    = not gui_clkout[ck]['BYP'] and gui_clkout[ck]['TRIM_EN']
                self.gui_clkout[ck]['TRIM_MODE'].hideopt    = not self.gui_clkout[ck]['TRIM_MODE'].editopt
                self.gui_clkout[ck]['TRIM_MODE'].usr_val    = gui_clkout[ck]['TRIM_MODE']
                self.gui_clkout[ck]['TRIM_MODE'].cal_val    = self.gui_clkout[ck]['TRIM_MODE'].def_val

                # Clock Trim Delay Multiplier
                self.gui_clkout[ck]['TRIM_MULT'].editopt    = not gui_clkout[ck]['BYP'] and gui_clkout[ck]['TRIM_EN']
                self.gui_clkout[ck]['TRIM_MULT'].hideopt    = not self.gui_clkout[ck]['TRIM_MULT'].editopt
                self.gui_clkout[ck]['TRIM_MULT'].usr_val    = gui_clkout[ck]['TRIM_MULT']
                self.gui_clkout[ck]['TRIM_MULT'].cal_val    = self.gui_clkout[ck]['TRIM_MULT'].def_val

        # ----------------------
        # Optional Ports
        # ----------------------

        # PLL RefClk from IO Pin
        self.gui_en_refclk_pin.usr_val                      = gui_en_refclk_pin

        # PLL RefClk IO Type
        self.gui_refclk_io_type.editopt                     = gui_en_refclk_pin
        self.gui_refclk_io_type.hideopt                     = not self.gui_refclk_io_type.editopt
        self.gui_refclk_io_type.usr_val                     = gui_refclk_io_type
        self.gui_refclk_io_type.cal_val                     = self.gui_refclk_io_type.def_val

        # Enable Dynamic Phase Ports
        self.gui_en_dyn_phase.editopt                       = 0 if(gui_reg_interface == 'APB' and gui_en_csr) else 1
        self.gui_en_dyn_phase.usr_val                       = gui_en_dyn_phase
        self.gui_en_dyn_phase.cal_val                       = 0

        # Enable PLL Reset Port
        self.gui_en_pll_reset.usr_val                       = gui_en_pll_reset

        # Enable PLL Lock Port
        self.gui_en_pll_lock.usr_val                        = gui_en_pll_lock

        # PLL Lock Sticky
        self.gui_pll_lock_sticky.editopt                    = gui_en_pll_lock
        self.gui_pll_lock_sticky.hideopt                    = not self.gui_pll_lock_sticky.editopt
        self.gui_pll_lock_sticky.usr_val                    = gui_pll_lock_sticky
        self.gui_pll_lock_sticky.cal_val                    = self.gui_pll_lock_sticky.def_val

        # Register interface
        self.gui_reg_interface.usr_val                      = gui_reg_interface

        # Enable CSR
        self.gui_en_csr.editopt                             = 1 if(gui_reg_interface == 'APB') else 0
        self.gui_en_csr.hideopt                             = not self.gui_en_csr.editopt
        self.gui_en_csr.usr_val                             = gui_en_csr
        self.gui_en_csr.cal_val                             = 0

        # Enable Legacy Mode
        self.gui_en_legacy.usr_val                          = gui_en_legacy

        # Enable Powerdown Port
        self.gui_en_powerdown.usr_val                       = gui_en_powerdown


        # -------------------------------------------------------------------------------------
        # Update RTL parameters
        # -------------------------------------------------------------------------------------
        self.rtl_params                                     = self.set_rtl_params()

        return "set_attr: done"
    # end def set_attr

    def changed_value(self, value_exp, value_obs):
        status = 0 if(value_exp == value_obs) else 1
        return status

    def calc_ssc_parameters(self,ssc_en,freq_phasedet,ssc_mod_freq,ssc_triangle,ssc_profile,n_div):
        log = self.log

        if(ssc_en):
            ssc_tbase        = int(round(1000.0*freq_phasedet/ssc_mod_freq))
            ssc_f_amp        = (ssc_triangle/100.0) if(ssc_profile == "DOWN") else (ssc_triangle/200.0)
            ssc_depth        = ssc_f_amp*n_div*262144/ssc_tbase
            if(ssc_depth > 127):
                ssc_depth_factor    = int(log(ssc_depth/127,2))+1 if(log(ssc_depth/127,2) % 1 > 0) else log(ssc_depth/127,2)
                ssc_weight_sel      = 1 if(ssc_depth_factor < 3) else int(ssc_depth_factor-2)
                ssc_step_in         = int(round(ssc_depth/(2**(ssc_weight_sel+2))))
            else:
                ssc_step_in         = int(round(ssc_depth))
                ssc_weight_sel      = 0
        else:
            ssc_tbase      = 0
            ssc_step_in    = 0
            ssc_weight_sel = 0
        return (ssc_tbase,ssc_step_in,ssc_weight_sel)

    def calc_trim(self, mode, del_mult):
        trim = "0b"
        if mode == "Rising":
            trim = trim + "1" + del_mult
        else:
            trim = trim + "0" + del_mult
        return trim

    def get_clk_o_range(self,clk_is_fbk):
        IDX_FOUT = 'FOUT_I' if(clk_is_fbk) else 'FOUT_F'
        clk_o_range = (self.PARAM_RANGE[IDX_FOUT]['MIN'],
                       self.PARAM_RANGE[IDX_FOUT]['MAX'])
        return clk_o_range

    def all_clkout_disabled_or_bypassed(self,gui_clkout={}):
        status = 1
        for ck in gui_clkout:
            if(gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']):
                status = 0
        return status

    def gen_fb_clk_opts(self,gui_en_frac_n,gui_en_ssc,gui_en_usr_fbk,gui_clkout={}):
        fb_clk_opts = []
        fb_int_clks = []
        if(gui_en_usr_fbk):
            fb_clk_opts.append(('User Feedback Clock','CLKOP'))
        elif(gui_en_frac_n or gui_en_ssc):
            fb_clk_opts.append(('Internal VCO','INTCLKOP'))
        else:
            for ck in gui_clkout:
                if(gui_clkout[ck]['EN'] and not gui_clkout[ck]['BYP']):
                    fb_clk_opts.append(ck)
                    fb_int_clks.append('INT'+ck)

            if(len(fb_clk_opts) == 0):
                fb_int_clks.append('INTCLKOP')

            fb_clk_opts.sort()
            fb_int_clks.sort()

        return fb_clk_opts+fb_int_clks

    def diff_is_close(self,value,expected,tol=1e-4,margin=0.001,round_factor=100):
        percent_factor = 100
        exp = expected if(expected > 0) else 1e-15
        Tol = tol if(tol > 0) else self.TOL_NEAR_ZERO
        diff   = round(self.abs(1-(1.0*value/expected))*percent_factor*round_factor)/round_factor
        result = 0 if(diff > ((Tol+margin)*(1+margin))) else 1
        return result

    def get_fbk_div_range(self,frac_n_en=0,ssc_en=0,mode='FREQUENCY',Fpfd=10.0):
        IDX_N_DIV = 'N_DIV_F' if(frac_n_en or ssc_en) else 'N_DIV_I'
        if(mode == 'FREQUENCY'):
            fbk_div_range = (self.PARAM_RANGE[IDX_N_DIV]['MIN'],
                             self.PARAM_RANGE[IDX_N_DIV]['MAX'])
        else:
            min_Fvco = self.PARAM_RANGE['FVCO']['MIN']
            max_Fvco = self.PARAM_RANGE['FVCO']['MAX']

            if(frac_n_en or ssc_en):
                lo_div_n = int(min_Fvco/Fpfd)+1 if(not frac_n_en and ssc_en and (min_Fvco % Fpfd) > 0) else int(min_Fvco/Fpfd)
                if(lo_div_n < self.PARAM_RANGE[IDX_N_DIV]['MIN']):
                    lo_div_n = self.PARAM_RANGE[IDX_N_DIV]['MIN']
                elif(lo_div_n > self.PARAM_RANGE[IDX_N_DIV]['MAX']):
                    lo_div_n = self.PARAM_RANGE[IDX_N_DIV]['MAX']

                hi_div_n = int(max_Fvco/Fpfd)
                if(hi_div_n < self.PARAM_RANGE[IDX_N_DIV]['MIN']):
                    hi_div_n = self.PARAM_RANGE[IDX_N_DIV]['MIN']
                elif(hi_div_n > self.PARAM_RANGE[IDX_N_DIV]['MAX']):
                    hi_div_n = self.PARAM_RANGE[IDX_N_DIV]['MAX']

                fbk_div_range = (lo_div_n,hi_div_n)
            else:
                # N*O = Fvco/Fpfd, highest N when O is minimum and Fout is maximum
                hi_div_n = int(min_Fvco/Fpfd)
                if(hi_div_n < self.PARAM_RANGE[IDX_N_DIV]['MIN']):
                    hi_div_n = self.PARAM_RANGE[IDX_N_DIV]['MIN']
                elif(hi_div_n > self.PARAM_RANGE[IDX_N_DIV]['MAX']):
                    hi_div_n = self.PARAM_RANGE[IDX_N_DIV]['MAX']

                fbk_div_range = (self.PARAM_RANGE[IDX_N_DIV]['MIN'],hi_div_n)

        return fbk_div_range

    def get_refck_div_range(self,Fref,frac_n_en=0,ssc_en=0,Fout=0,Tol=0):
        if(check_is_jp_device()):
            IDX_FPFD = 'FPFD_JP'        
        else:
            IDX_FPFD = 'FPFD_F' if(frac_n_en or ssc_en) else 'FPFD_I'

        if(not frac_n_en and not ssc_en and Fout > 0 and Tol == 0):
            min_div_m = int(Fref/Fout) if(Fref > Fout) else self.PARAM_RANGE['M_DIV']['MIN']
        else:
            min_div_m = int((Fref+self.PARAM_RANGE[IDX_FPFD]['MAX']-1)/self.PARAM_RANGE[IDX_FPFD]['MAX'])
            if(Fref/min_div_m > self.PARAM_RANGE[IDX_FPFD]['MAX']):
                min_div_m = min_div_m+1
        refck_div_range = (min_div_m,int(Fref/self.PARAM_RANGE[IDX_FPFD]['MIN']))
        return refck_div_range

    def get_div_out_range(self,Fout,Tol=1e-4):
        min_Fvco     = self.PARAM_RANGE['FVCO']['MIN']
        max_Fvco     = self.PARAM_RANGE['FVCO']['MAX']

        # Calculate range of valid output divider
        min_div_o    = int(min_Fvco/(Fout*(1+Tol/100.0)))
        max_div_o    = int(max_Fvco/(Fout*(1-Tol/100.0)))
        max_div_o_r  = max_Fvco % Fout
        if(min_div_o >= self.PARAM_RANGE['O_DIV']['MAX']):
            min_O_DIV = self.PARAM_RANGE['O_DIV']['MAX']
        else:
            if(min_div_o < self.PARAM_RANGE['O_DIV']['MIN']):
                min_div_o = self.PARAM_RANGE['O_DIV']['MIN']
            min_div_o_isclose = self.diff_is_close(value=min_Fvco,expected=(min_div_o*Fout),tol=Tol)
            min_O_DIV = min_div_o if(min_div_o_isclose) else (min_div_o+1)

        if(max_div_o >= self.PARAM_RANGE['O_DIV']['MAX']):
            max_O_DIV = self.PARAM_RANGE['O_DIV']['MAX']
        else:
            max_div_o_isclose = self.diff_is_close(value=max_Fvco,expected=((max_div_o+1)*Fout),tol=Tol)
            max_O_DIV = max_div_o+1 if(max_div_o_r > 0 and max_div_o_isclose) else max_div_o

        return (min_O_DIV,max_O_DIV)

    def get_vco_range(self,Fout,tol=1e-4):
        min_Fvco     = self.PARAM_RANGE['FVCO']['MIN']
        max_Fvco     = self.PARAM_RANGE['FVCO']['MAX']

        vco_range = {}
        Tol = tol if(tol > 0) else self.TOL_NEAR_ZERO
        (min_div_o,max_div_o) = self.get_div_out_range(Fout,Tol)
        for div_o in range(min_div_o, max_div_o+1):
            lo_fvco = div_o*Fout*(1-Tol/100.0)
            hi_fvco = div_o*Fout*(1+Tol/100.0)
            valid_lo_fvco = 1
            valid_hi_fvco = 1
            if(lo_fvco < min_Fvco):
                lo_fvco_isclose = self.diff_is_close(value=lo_fvco,expected=min_Fvco,tol=0)
                lo_fvco = min_Fvco
                if(not lo_fvco_isclose):
                    valid_lo_fvco = 0
            elif(lo_fvco > max_Fvco):
                lo_fvco_isclose = self.diff_is_close(value=lo_fvco,expected=max_Fvco,tol=0)
                lo_fvco = max_Fvco
                if(not lo_fvco_isclose):
                    valid_lo_fvco = 0

            if(hi_fvco < min_Fvco):
                hi_fvco_isclose = self.diff_is_close(value=hi_fvco,expected=min_Fvco,tol=0)
                hi_fvco = min_Fvco
                if(not hi_fvco_isclose):
                    valid_hi_fvco = 0
            elif(hi_fvco > max_Fvco):
                hi_fvco_isclose = self.diff_is_close(value=hi_fvco,expected=max_Fvco,tol=0)
                hi_fvco = max_Fvco
                if(not hi_fvco_isclose):
                    valid_hi_fvco = 0
            if(valid_lo_fvco or valid_hi_fvco):
                vco_range[div_o] = (lo_fvco,hi_fvco)

        return vco_range

    def get_intersect(self,a=[],b=[]):
        common_range = set()
        if(len(a) and len(b)):
            for i in a:
                for j in b:
                    if((j[0] <= i[0] and i[0] <= j[1]) or
                       (j[0] <= i[1] and i[1] <= j[1]) or
                       (j[0] <= i[0] and i[1] <= j[1]) or
                       (i[0] <= j[0] and j[1] <= i[1])):
                        common_range.add(( max([i[0],j[0]]),
                                           min([i[1],j[1]])
                                         ))
        return list(common_range)

    def get_div_o_list_common(self,vco_range_list,Fout,div_o_range,Tol=1e-4):
        div_o_set = set()
        for (vco_lo,vco_hi) in vco_range_list:
            lo_div_o  = int(vco_lo/Fout)
            lo_div_o_isclose = self.diff_is_close(value=(lo_div_o*Fout),expected=vco_lo,tol=Tol)
            if(not lo_div_o_isclose):
                lo_div_o = lo_div_o+1

            hi_div_o  = int(vco_hi/Fout)+1 if(vco_hi % Fout > 0) else int(vco_hi/Fout)
            hi_div_o_isclose = self.diff_is_close(value=(hi_div_o*Fout),expected=vco_hi,tol=Tol)
            if(not hi_div_o_isclose):
                hi_div_o = hi_div_o-1

            div_o_set = div_o_set | set([div_o for div_o in range(lo_div_o,hi_div_o+1)
                                               if(div_o_range[0] <= div_o and div_o <= div_o_range[1])])

        return list(div_o_set)

    def calc_int_dividers(self,Fref,fbk_name,Fout_d,Tol_d):

        # Calculate range of valid reference clock divider
        (min_M_DIV,max_M_DIV) = self.get_refck_div_range(Fref)

        min_Fvco  = self.PARAM_RANGE['FVCO']['MIN']
        max_Fvco  = self.PARAM_RANGE['FVCO']['MAX']
        min_N_DIV = self.PARAM_RANGE['N_DIV_I']['MIN']
        max_N_DIV = self.PARAM_RANGE['N_DIV_I']['MAX']

        vco_range    = {}
        div_o_range  = {}
        common_range = []
        initial_done = 0
        for ck in Fout_d:
            #Calculate range of output dividers
            div_o_range[ck] = self.get_div_out_range(Fout_d[ck],Tol_d[ck])
            # Calculate range of valid vco frequency
            vco_range[ck]  = self.get_vco_range(Fout_d[ck],Tol_d[ck])
            # Get the intersection of VCO frequency range
            if(initial_done):
                common_range = self.get_intersect(common_range,[vco_range[ck][div_key] for div_key in vco_range[ck]])
            else:
                common_range = [vco_range[ck][div_key] for div_key in vco_range[ck]]
                initial_done = 1

        MNO_DIV_LIST = {}
        N_DIV_LIST   = []
        M_DIV_LIST   = []
        O_DIV_LIST   = {}

        if(len(common_range)):
            n_div_set  = set()
            m_div_set  = set()
            o_div_set  = {}

            div_o_list_common = self.get_div_o_list_common(common_range,Fout_d[fbk_name],
                                                           div_o_range[fbk_name],Tol_d[fbk_name])

            N_over_M  = Fout_d[fbk_name] / Fref
            if(N_over_M >= 1):
                min_m_div = min_M_DIV
            else:
                min_m_div = min_M_DIV if(min_M_DIV > min_N_DIV) else (min_N_DIV if(min_N_DIV < max_M_DIV) else max_M_DIV)

            # Search for valid combinations of dividers
            for div_m in range(min_m_div,max_M_DIV+1):
                # reduce the loop on divider N by calculating the valid range of N with the given ratio
                if(N_over_M >= 1):
                    max_n_div = max_N_DIV
                    if(div_m > max_N_DIV):
                        min_n_div = max_N_DIV
                    else:
                        div_m_isclose = self.diff_is_close(value=(div_m-1),expected=div_m,tol=Tol_d[fbk_name])
                        min_n_div = div_m if((div_m == min_M_DIV) or not div_m_isclose) else (div_m-1)
                else:
                    min_n_div = min_N_DIV
                    if(div_m < max_N_DIV):
                        div_m_isclose = self.diff_is_close(value=(div_m-1),expected=div_m,tol=Tol_d[fbk_name])
                        max_n_div = div_m if((div_m == max_M_DIV) or not div_m_isclose) else (div_m+1)
                    else:
                        max_n_div = max_N_DIV
                valid_n = 0
                for div_n in range(min_n_div,max_n_div+1):
                    div_n_isclose = self.diff_is_close(value=div_n,expected=(div_m*N_over_M),tol=Tol_d[fbk_name])
                    if(div_n_isclose):
                        valid_fbk_div_o = 0
                        o_list = {}
                        for fbk_div_o in div_o_list_common:
                            fvco_actual = Fref*div_n*fbk_div_o/div_m
                            if(self.PARAM_RANGE['FVCO']['MIN'] <= fvco_actual and
                               fvco_actual <= self.PARAM_RANGE['FVCO']['MAX']):
                                valid_div_o = 1
                                o_list_tmp = {}
                                for ck in [fout_name for fout_name in Fout_d if(fout_name != fbk_name)]:
                                    div_o    = fvco_actual/Fout_d[ck]
                                    lo_div_o = int(div_o) if(div_o > 1) else 1
                                    hi_div_o = (int(div_o)+1) if((div_o % 1) > 0) else int(div_o)
                                    lo_div_o_isclose = self.diff_is_close(value=fvco_actual,
                                                                          expected=(lo_div_o*Fout_d[ck]),
                                                                          tol=Tol_d[ck])
                                    hi_div_o_isclose = self.diff_is_close(value=fvco_actual,
                                                                          expected=(hi_div_o*Fout_d[ck]),
                                                                          tol=Tol_d[ck])
                                    if(div_o > self.PARAM_RANGE['O_DIV']['MAX']):
                                        valid_div_o = 0
                                        break
                                    else:
                                        if(lo_div_o_isclose):
                                            if(ck in o_list_tmp):
                                                o_list_tmp[ck] = o_list_tmp[ck] | set([lo_div_o,hi_div_o] if(hi_div_o_isclose) else [lo_div_o])
                                            else:
                                                o_list_tmp[ck] = set([lo_div_o,hi_div_o] if(hi_div_o_isclose) else [lo_div_o])
                                        elif(hi_div_o_isclose):
                                            if(ck in o_list_tmp):
                                                o_list_tmp[ck] = o_list_tmp[ck] | set([hi_div_o])
                                            else:
                                                o_list_tmp[ck] = set([hi_div_o])
                                        else:
                                            valid_div_o = 0
                                            break
                                if(valid_div_o):
                                    if(fbk_name in o_list):
                                        o_list[fbk_name] = o_list[fbk_name] | set([fbk_div_o])
                                    else:
                                        o_list[fbk_name] = set([fbk_div_o])
                                    for ck in [fout_name for fout_name in Fout_d if(fout_name != fbk_name)]:
                                        if(ck in o_list):
                                            o_list[ck] = o_list[ck] | o_list_tmp[ck]
                                        else:
                                            o_list[ck] = o_list_tmp[ck]
                                    valid_fbk_div_o  = 1
                        if(valid_fbk_div_o):
                            m_div_set.add(div_m)
                            n_div_set.add(div_n)
                            for ck in o_list:
                                if(ck in o_div_set):
                                    o_div_set[ck] = o_div_set[ck] | o_list[ck]
                                else:
                                    o_div_set[ck] = o_list[ck]
                                o_list[ck] = list(o_list[ck])
                                o_list[ck].sort()

                            if(div_m in MNO_DIV_LIST):
                                MNO_DIV_LIST[div_m][div_n] = {}
                                MNO_DIV_LIST[div_m][div_n] = o_list
                            else:
                                MNO_DIV_LIST[div_m] = {}
                                MNO_DIV_LIST[div_m][div_n] = {}
                                MNO_DIV_LIST[div_m][div_n] = o_list
            N_DIV_LIST = list(n_div_set)
            N_DIV_LIST.sort()
            M_DIV_LIST = list(m_div_set)
            M_DIV_LIST.sort()
            for ck in o_div_set:
                O_DIV_LIST[ck] = list(o_div_set[ck])
                O_DIV_LIST[ck].sort()

        return (MNO_DIV_LIST,N_DIV_LIST,M_DIV_LIST,O_DIV_LIST)

    def calc_fracN_divider(self,Fref,Fout_d,Tol_d,frac_n_en=1,ssc_en=0):
        round = self.round
        # Calculate range of valid reference clock divider
        (min_M_DIV,max_M_DIV) = self.get_refck_div_range(Fref,frac_n_en=1)

        min_Fvco     = self.PARAM_RANGE['FVCO']['MIN']
        max_Fvco     = self.PARAM_RANGE['FVCO']['MAX']
        min_N_DIV    = self.PARAM_RANGE['N_DIV_F']['MIN']
        max_N_DIV    = self.PARAM_RANGE['N_DIV_F']['MAX']

        vco_range    = {}
        common_range = []
        initial_done = 0
        for ck in Fout_d:
            # Calculate range of valid VCO frequency
            vco_range[ck]  = self.get_vco_range(Fout_d[ck],Tol_d[ck])
            # Get the intersection of VCO frequency range
            if(initial_done):
                common_range = self.get_intersect(common_range,[vco_range[ck][div_key] for div_key in vco_range[ck]])
            else:
                common_range = [vco_range[ck][div_key] for div_key in vco_range[ck]]
                initial_done = 1

        MNO_DIV_LIST = {}
        N_DIV_LIST   = []
        M_DIV_LIST   = []
        O_DIV_LIST   = {}

        if(len(common_range)):
            n_div_set  = set()
            m_div_set  = set()
            o_div_set  = {}
            for (vco_lo,vco_hi) in common_range:
                vco   = 1.0*(vco_lo + vco_hi)/2
                for div_m in range(min_M_DIV,max_M_DIV+1):
                    div_fn = int(round(4096.0*vco*div_m/Fref))
                    div_n  = div_fn/4096.0
                    if(not frac_n_en and ssc_en):
                        # SSC will reuse same algorithm but N is integer
                        div_n_0 = int(div_n) if(div_n > 1) else 1
                        div_n_1 = (div_n_0 + 1)
                        vco_0   = Fref*div_n_0/div_m
                        vco_1   = Fref*div_n_1/div_m
                        if(vco_lo <= vco_0 and vco_0 <= vco_hi):
                            div_n = div_n_0
                        elif(vco_lo <= vco_1 and vco_1 <= vco_hi):
                            div_n = div_n_1
                        else:
                            div_n = 0
                    vco_actual = Fref*div_n/div_m
                    if(min_N_DIV <= div_n and div_n <= max_N_DIV):
                        o_list = {}
                        valid_div_o = 1
                        for ck in Fout_d:
                            lo_div_o         = int(vco_actual/Fout_d[ck])
                            hi_div_o         = lo_div_o if(vco_actual % Fout_d[ck] == 0) else (lo_div_o+1)
                            lo_div_o_isclose = 0 if(self.abs(1-(vco_actual/lo_div_o/Fout_d[ck])) > Tol_d[ck]) else 1
                            hi_div_o_isclose = 0 if(self.abs(1-(vco_actual/hi_div_o/Fout_d[ck])) > Tol_d[ck]) else 1
                            if(lo_div_o > self.PARAM_RANGE['O_DIV']['MAX']):
                                valid_div_o = 0
                                break
                            else:
                                if(lo_div_o_isclose):
                                    o_list[ck] = list(set({lo_div_o,hi_div_o})) if(hi_div_o_isclose and hi_div_o <= self.PARAM_RANGE['O_DIV']['MAX']) else [lo_div_o]
                                elif(hi_div_o_isclose and hi_div_o <= self.PARAM_RANGE['O_DIV']['MAX']):
                                    o_list[ck] = [hi_div_o]
                                else:
                                    # nullify all if there is 1 output that cannot be generated
                                    valid_div_o = 0
                                    break
                        if(valid_div_o):
                            m_div_set.add(div_m)
                            n_div_set.add(div_n)
                            for ck in o_list:
                                for div_o in o_list[ck]:
                                    if(ck in o_div_set):
                                        o_div_set[ck].add(div_o)
                                    else:
                                        o_div_set[ck] = set()
                                        o_div_set[ck].add(div_o)
                            if(div_m in MNO_DIV_LIST):
                                MNO_DIV_LIST[div_m][div_n] = {}
                                MNO_DIV_LIST[div_m][div_n] = o_list
                            else:
                                MNO_DIV_LIST[div_m] = {}
                                MNO_DIV_LIST[div_m][div_n] = {}
                                MNO_DIV_LIST[div_m][div_n] = o_list
            N_DIV_LIST = list(n_div_set)
            N_DIV_LIST.sort()
            M_DIV_LIST = list(m_div_set)
            M_DIV_LIST.sort()
            for ck in o_div_set:
                O_DIV_LIST[ck] = list(o_div_set[ck])
                O_DIV_LIST[ck].sort()

        return (MNO_DIV_LIST,N_DIV_LIST,M_DIV_LIST,O_DIV_LIST)

    def check_valid_freq_output(self,clk_name,mode='FREQUENCY',check_div1_clk0=0):
        status_ok = 1
        if(self.gui_clkout[clk_name]['EN'].usr_val and not self.gui_clkout[clk_name]['BYP'].usr_val):
            if(mode == 'FREQUENCY'):
                if(self.invalid_mno and check_div1_clk0 == 0):
                    status_ok = 0
                elif(check_div1_clk0 == 0):
                    status_ok = self.diff_is_close(value=self.gui_clkout[clk_name]['FREQ'].cal_val,
                                                   expected=self.gui_clkout[clk_name]['FREQ'].usr_val,
                                                   tol=self.gui_clkout[clk_name]['TOL'].usr_val)
            else:
                if(check_div1_clk0 == 1):
                    status_ok = 1
        if(not status_ok):
            PluginUtil.post_error("The desired frequency for %s with tolerance=%f cannot be generated.Try changing the tolerance or desired frequency." %
            (clk_name,self.gui_clkout[clk_name]['TOL'].usr_val))
        return status_ok

    def calc_ppm(self, exp_freq, act_freq):
        ppm = int(((self.abs(float(exp_freq) - float(act_freq)))/float(exp_freq)) * 1000000.0)
        return ppm


    def calc_del_phase_setting(self,div_out=1,phase_shift=45):
        div             = div_out-1
        phase_shift_idx = self.STATIC_PHASE_SHIFT.index(phase_shift)
        done            = 0
        phase_set       = (0,0)
        for ph in range(8):
            delx_ofst = phase_shift_idx*(div+1)-ph
            if(delx_ofst % 8 == 0):
                delx = delx_ofst//8 + div
                if(delx < 128):
                    phase_set = (delx,ph)
                    done = 1
                    break
        if(not done):
            for ph in range(8):
                delx_ofst = (8-phase_shift_idx)*(div+1)+ph
                if(delx_ofst % 8 == 0):
                    delx = div-delx_ofst//8
                    phase_set = (delx,ph)
                    done = 1
                    break
        return {'DEL':phase_set[0], 'PHI':phase_set[1]}

    def get_ref_count_value(self, div_ratio):
        abs = self.abs
        if((div_ratio > 0.3) or (abs(div_ratio - 0.3) <= 1e-5)):
            ref_count = 0
        elif((div_ratio < 0.3) and ((div_ratio > 0.125) or (abs(div_ratio - 0.125) <= 1e-5))):
            ref_count = 1
        elif((div_ratio < 0.125) and ((div_ratio > 0.06) or (abs(div_ratio - 0.06) <= 1e-5))):
            ref_count = 2
        elif((div_ratio < 0.06) and ((div_ratio > 0.03) or (abs(div_ratio - 0.03) <= 1e-5))):
            ref_count = 2
        else:
            ref_count = 4
        return ref_count

    def get_fbkdiv_list(self,mno_dict,fbk_name='CLKOP',frac_n_ssc_en=0):
        fbk_m = {}
        for m in mno_dict:
            for n in mno_dict[m]:
                if(frac_n_ssc_en):
                    fbkdiv = n
                    if fbkdiv in fbk_m:
                        fbk_m[fbkdiv][m] = mno_dict[m][n]
                    else:
                        fbk_m[fbkdiv] = {}
                        fbk_m[fbkdiv][m] = {}
                        fbk_m[fbkdiv][m] = mno_dict[m][n]
                else:
                    for o in mno_dict[m][n][fbk_name]:
                        fbkdiv = n*o
                        if fbkdiv in fbk_m:
                            fbk_m[fbkdiv][m] = (n,o)
                        else:
                            fbk_m[fbkdiv] = {}
                            fbk_m[fbkdiv][m] = {}
                            fbk_m[fbkdiv][m] = (n,o)

        fbkdiv_list = list(fbk_m.keys())
        fbkdiv_list.sort()
        return (fbkdiv_list,fbk_m)

    #def get_fbkdiv_list_vcoprio(self,mno_dict,fbk_name='CLKOP',frac_n_ssc_en=0,opt_prio=None):
    #    fbk_m       = {}
    #    best_div    = {}
    #    for m in mno_dict:
    #        for n in mno_dict[m]:
    #            if(frac_n_ssc_en):
    #                fbkdiv = n
    #                ratio  = int(1e6*fbkdiv/m)
    #                if ratio not in best_div:
    #                    best_div[ratio] = []
    #                best_div[ratio] = best_div[ratio] + [(m,fbkdiv)]

    #            else:
    #                for o in mno_dict[m][n][fbk_name]:
    #                    fbkdiv = n*o
    #                    ratio  = int(1e6*fbkdiv/m)
    #                    if ratio not in best_div:
    #                        best_div[ratio] = []
    #                    best_div[ratio] = best_div[ratio] + [(m,fbkdiv,o)]


    #    # get best divider ratio
    #    best_ratio  = min(best_div) if(opt_prio == 'POWER') else max(best_div)
    #    # get divider set with minimum refclk divider
    #    sel_div_set = min(best_div[best_ratio])
    #    m_div       = sel_div_set[0]
    #    fbkdiv      = sel_div_set[1]
    #    fbkdiv_list = [fbkdiv]

    #    fbk_m[fbkdiv] = {}
    #    fbk_m[fbkdiv][m_div] = {}
    #    if(frac_n_ssc_en):
    #        fbk_m[fbkdiv][m_div] = fbkdiv
    #    else:
    #        o_div = sel_div_set[2]
    #        n_div = fbkdiv//o_div
    #        fbk_m[fbkdiv][m_div] = (n_div,o_div)

    #    return (fbkdiv_list,fbk_m)

    def get_fbkdiv_list_pfdprio(self,mno_dict,fbk_name='CLKOP',frac_n_ssc_en=0,opt_prio='JITTER',gui_refclk_freq=100):
        fbk_m    = {}
        best_div = {}
        # get lowest refclk divider (High PFD)
        m_div  = min(mno_dict)
        # total feedback divider depends if fractional-N/SSC is enabled
        # get feedback divider based on target optimization priority
        n_div  = None
        o_div  = None
        if(frac_n_ssc_en):
            n_div  = min(mno_dict[m_div]) if(opt_prio == 'POWER') else max(mno_dict[m_div])
            fbkdiv = n_div
        else:
            lst_no = [(n*o,n,o) for n in mno_dict[m_div] \
                                    for o in mno_dict[m_div][n][fbk_name] \
                                        if(not (n*o*gui_refclk_freq/m_div == 800 and o == 1))] # cannot use output div 1 when VCO is 800 (in feedback clock)
            sel_no = min(lst_no) if(opt_prio == 'POWER') else max(lst_no)
            o_div  = sel_no[2]
            n_div  = sel_no[1]
            fbkdiv = sel_no[0]

        fbkdiv_list = [fbkdiv]

        fbk_m[fbkdiv] = {}
        fbk_m[fbkdiv][m_div] = {}
        if(frac_n_ssc_en):
            fbk_m[fbkdiv][m_div] = fbkdiv
        else:
            fbk_m[fbkdiv][m_div] = (n_div,o_div)

        return (fbkdiv_list,fbk_m)

    def get_max_ahg3(self,fbk_div,coef):
        log10 = self.log10
        abs   = self.abs

        prev_ahg3 = 0
        prev_k = 60
        start = 0
        for i in range(1,4):
            for k in self.s_list_keys[start:]:
                (f,s,s_2,k_idx) = self.s_list[k]
                lg3  = (coef['C1']*s_2 + coef['C2']*s + coef['C3']) / \
                       (fbk_div*s_2*(coef['C4']*s_2 + coef['C5']*s + coef['C6']))
                ahg3 = 20*log10(abs(lg3/(1+lg3)))
                # check if ahg3 value changes from hi to low
                if(prev_ahg3 > ahg3):
                    if(i < 3):
                        start = self.s_list[prev_k*10][3]
                    break
                else:
                    prev_k = k
                    prev_ahg3 = ahg3
        return prev_ahg3

    def interpolate_ahg3_freq(self,fbk_div,coef):
        log10     = self.log10
        abs       = self.abs

        prev_f    = 1e6
        prev_ahg3 = 0
        prev_k    = 60
        start     = 0
        for i in range(1,4):
            for k in self.s_list_keys[start:]:
                (f,s,s_2,k_idx) = self.s_list[k]
                lg3  = (coef['C1']*s_2 + coef['C2']*s + coef['C3']) / \
                       (fbk_div*s_2*(coef['C4']*s_2 + coef['C5']*s + coef['C6']))
                ahg3 = 20*log10(abs(lg3/(1+lg3)))
                # check if ahg3 is less than -3
                if(ahg3+3 < 0):
                    if(i < 3):
                        start = self.s_list[prev_k*10][3]
                    break
                else:
                    prev_k    = k
                    prev_ahg3 = ahg3
                    prev_f    = f

        if(abs(prev_ahg3+3) < abs(ahg3+3)):
            final_f    = prev_f
        else:
            final_f    = f
        return final_f

    def interpolate_alg3_freq(self,fbk_div,coef):
        log10     = self.log10
        phase     = self.phase
        abs       = self.abs

        prev_f    = 1e6
        prev_alg3 = 0
        prev_lg3  = 0
        prev_k    = 60
        start     = 0
        for i in range(1,4):
            for k in self.s_list_keys[start:]:
                (f,s,s_2,k_idx) = self.s_list[k]
                lg3  = (coef['C1']*s_2 + coef['C2']*s + coef['C3']) / \
                       (fbk_div*s_2*(coef['C4']*s_2 + coef['C5']*s + coef['C6']))
                alg3 = 20*log10(abs(lg3))
                # check if alg3 is less than 0
                if(alg3 < 0):
                    if(i < 3):
                        start = self.s_list[prev_k*10][3]
                    break
                else:
                    prev_k    = k
                    prev_alg3 = alg3
                    prev_f    = f
                    prev_lg3  = lg3

        if(abs(prev_alg3) < abs(alg3)):
            final_lg3 = prev_lg3
            final_f   = prev_f
        else:
            final_lg3 = lg3
            final_f   = f
        pm = phase(-final_lg3)*self.d180_overPI
        result = {'f':final_f,'phase':pm}
        return result

    #def calc_response(self,n_list,fbk_m_dict,fref=100e6):
    #    self.valid_response = {}
    #    self.best_response  = {}
    #    coef_key_list       = list(self.func_coef.keys())
    #    coef_key_list.sort()
    #    for n in n_list:
    #        best_bw_3db = 0
    #        best_param  = (('fbk_div',n),)
    #        for coef_key in coef_key_list: # 8192 loops
    #            coef = self.func_coef[coef_key]
    #            peak = self.get_max_ahg3(n,coef)
    #            if(peak >= self.PARAM_RANGE['PEAK']['MIN'] and
    #               peak <= self.PARAM_RANGE['PEAK']['MAX']):
    #                min_alg3_f  = self.interpolate_alg3_freq(n,coef)
    #                op_loop_bw  = min_alg3_f['f']
    #                pm_3db      = min_alg3_f['phase']
    #                if(pm_3db > self.PARAM_RANGE['PM_3DB']['MIN']):
    #                    bw_3db  = self.interpolate_ahg3_freq(n,coef)
    #                    m_div   = 0
    #                    if(self.bypass_bw_factor):
    #                        m_div = min(fbk_m_dict[n])
    #                    else:
    #                        for m in fbk_m_dict[n]:
    #                            bw_factor = fref/m/bw_3db
    #                            if(bw_factor >= self.PARAM_RANGE['BWFACTOR']['MIN']):
    #                                m_div = m
    #                                break
    #                    if(m_div > 0):
    #                        rsp_key = ((('fbk_div',n),('m_div',m_div),) + coef_key)
    #                        self.valid_response[rsp_key] = {'PEAK':peak,
    #                                                        'BW_3DB':bw_3db*1e-6,
    #                                                        'BW_OPL':op_loop_bw*1e-6,
    #                                                        'PM_3DB':pm_3db}
    #                        if(bw_3db > best_bw_3db):
    #                            best_bw_3db = bw_3db
    #                            best_param  = rsp_key

    #        if(best_bw_3db > 0):
    #            self.best_response[n] = {'BW_3DB':best_bw_3db*1e-6, 'PARAM':best_param}
    #            break
    #    return self.best_response

    # priority - best bw_3db
    #def calc_response(self,n_list,fbk_m_dict,fref=100e6):
    #    self.valid_response = {}
    #    self.best_response  = {}
    #    coef_key_list       = list(self.func_coef.keys())
    #    coef_key_list.sort()
    #    [f,s,s_2]           = self.s_list
    #    PI                  = 3.1415926535897932384626433832795
    #    np                  = self.np
    #    for n in n_list:
    #        best_bw_3db = 0
    #        best_param  = (('fbk_div',n),)
    #        for coef_key in coef_key_list: # 8192 loops
    #            coef = self.func_coef[coef_key]
    #            lg3  = (coef['C1']*s_2 + coef['C2']*s + coef['C3']) / \
    #                   (n*s_2*(coef['C4']*s_2 + coef['C5']*s + coef['C6']))
    #            ahg3 = 20*np.log10(np.abs(lg3/(1+lg3)))

    #            peak = ahg3.max()

    #            if(peak >= self.PARAM_RANGE['PEAK']['MIN'] and
    #               peak <= self.PARAM_RANGE['PEAK']['MAX']):
    #                alg3        = 20*np.log10(np.abs(lg3))
    #                plg3        = np.angle(-lg3) / PI * 180

    #                op_loop_bw  = f[(np.abs(alg3)).argmin()]
    #                pm_3db_idx  = (np.abs(f-op_loop_bw)).argmin()
    #                pm_3db      = plg3[pm_3db_idx]

    #                if(pm_3db > self.PARAM_RANGE['PM_3DB']['MIN']):
    #                    bw_3db  = f[(np.abs(ahg3+3)).argmin()]
    #                    m_div   = 0
    #                    for m in fbk_m_dict[n]:
    #                        bw_factor = fref/m/bw_3db
    #                        if(bw_factor >= self.PARAM_RANGE['BWFACTOR']['MIN']):
    #                            m_div = m
    #                            break
    #                    if(m_div > 0):
    #                        rsp_key = ((('fbk_div',n),('m_div',m_div),) + coef_key)
    #                        self.valid_response[rsp_key] = {'PEAK':peak,
    #                                                        'BW_3DB':bw_3db*1e-6,
    #                                                        'BW_OPL':op_loop_bw*1e-6,
    #                                                        'PM_3DB':pm_3db}
    #                        if(bw_3db > best_bw_3db):
    #                            best_bw_3db = bw_3db
    #                            best_param  = rsp_key

    #        if(best_bw_3db > 0):
    #            self.best_response[n] = {'BW_3DB':best_bw_3db*1e-6, 'PARAM':best_param}
    #    return self.best_response

    # priority - best pm_3db
    def calc_response(self,n_list,fbk_m_dict,fref=100e6):
        self.valid_response = {}
        self.best_response  = {}
        coef_key_list       = list(self.func_coef.keys())
        coef_key_list.sort()
        [f,s,s_2]           = self.s_list
        PI                  = 3.1415926535897932384626433832795
        np                  = self.np
        for n in n_list:
            best_pm_3db = 0
            best_bw_3db = 0
            best_param  = (('fbk_div',n),)
            for coef_key in coef_key_list: # 8192 loops
                coef = self.func_coef[coef_key]
                lg3  = (coef['C1']*s_2 + coef['C2']*s + coef['C3']) / \
                       (n*s_2*(coef['C4']*s_2 + coef['C5']*s + coef['C6']))
                ahg3 = 20*np.log10(np.abs(lg3/(1+lg3)))

                peak = ahg3.max()

                if(peak >= self.PARAM_RANGE['PEAK']['MIN'] and
                   peak <= self.PARAM_RANGE['PEAK']['MAX']):
                    alg3        = 20*np.log10(np.abs(lg3))
                    plg3        = np.angle(-lg3) / PI * 180

                    op_loop_bw  = f[(np.abs(alg3)).argmin()]
                    pm_3db_idx  = (np.abs(f-op_loop_bw)).argmin()
                    pm_3db      = plg3[pm_3db_idx]

                    if(pm_3db > self.PARAM_RANGE['PM_3DB']['MIN']):
                        bw_3db  = f[(np.abs(ahg3+3)).argmin()]
                        m_div   = 0
                        for m in fbk_m_dict[n]:
                            bw_factor = fref/m/bw_3db

                            # pick maximum charge pump current for low PFD frequencies
                            if(fref/m <= 100e6):
                                ip = self.valid_ip_i2[coef_key[0:4]]['ip']
                                if(ip < 0.0003): # if proportional current is less than maximum possible value
                                    break # disreguard parameter set
                                bw_factor_min = self.PARAM_RANGE['BWFACTOR_LF']['MIN']
                            else:
                                bw_factor_min = self.PARAM_RANGE['BWFACTOR_HF']['MIN']

                            if(bw_factor >= bw_factor_min):
                                m_div = m
                                break
                        if(m_div > 0):
                            rsp_key = ((('fbk_div',n),('m_div',m_div),) + coef_key)
                            self.valid_response[rsp_key] = {'PEAK':peak,
                                                            'BW_3DB':bw_3db*1e-6,
                                                            'BW_OPL':op_loop_bw*1e-6,
                                                            'PM_3DB':pm_3db}
                            if(pm_3db > best_pm_3db):
                                best_pm_3db = bw_3db
                                best_bw_3db = bw_3db
                                best_param  = rsp_key

            if(best_pm_3db > 0):
                self.best_response[n] = {'PM_3DB':best_pm_3db, 'BW_3DB':best_bw_3db*1e-6, 'PARAM':best_param}
        return self.best_response

    def get_final_param(self):
        best_param              = {}

        gui_refclk_freq         = self.gui_refclk_freq.usr_val
        gui_optim_prio          = self.gui_optim_prio.usr_val if(self.gui_optim_prio.editopt) else \
                                  self.gui_optim_prio.cal_val
        gui_fbk_mode            = self.gui_fbk_mode.usr_val if(self.gui_fbk_mode.editopt) else \
                                  self.gui_fbk_mode.cal_val
        gui_en_frac_n           = self.gui_en_frac_n.usr_val if(self.gui_en_frac_n.editopt) else \
                                  self.gui_en_frac_n.cal_val
        gui_en_ssc              = self.gui_en_ssc.usr_val if(self.gui_en_ssc.editopt) else \
                                  self.gui_en_ssc.cal_val

        fref                    = gui_refclk_freq*1e6*1.0
        fbk_name                = gui_fbk_mode.replace('INT','')

        frac_n_ssc_en           = gui_en_frac_n | gui_en_ssc

        mno_dict                = self.mno_dict

        # select best set of dividers based on optimization priority
        (n_list,fbk_m_dict)     = self.get_fbkdiv_list_pfdprio(mno_dict,fbk_name,frac_n_ssc_en,
                                                               gui_optim_prio,gui_refclk_freq)
        #print("[DEBUG] n_list = {}".format(n_list))
        #print("[DEBUG] fbk_m_dict = {}".format(fbk_m_dict))

        #n_lim_idx               = (len(n_list)-self.N_ITER_MAX) if(len(n_list) > self.N_ITER_MAX) else 0
        #best_resp_dict          = self.calc_response(n_list[n_lim_idx:],fbk_m_dict,fref)
        best_resp_dict          = self.calc_response(n_list,fbk_m_dict,fref)

        best_bw_3db             = 0
        best_pm_3db             = 0
        best_mn                 = ()
        prev_n                  = 0
        for n in best_resp_dict:
            pm_3db              = best_resp_dict[n]['PM_3DB']
            bw_3db              = best_resp_dict[n]['BW_3DB']
            #print("[DEBUG] best_resp_dict[{}] = {}".format(n,best_resp_dict[n]))
            #print("[DEBUG] valid_response[{}] = {}".format(n,self.valid_response[best_resp_dict[n]['PARAM']]))
            if(n >= prev_n):
                #if(bw_3db >= best_bw_3db):
                # priority : pm_3db
                if(pm_3db >= best_pm_3db):
                    best_pm_3db     = pm_3db
                    best_bw_3db     = bw_3db
                    best_mn         = (dict(best_resp_dict[n]['PARAM'])['m_div'],n)
            prev_n              = n

        if(len(best_mn)):
            m_div               = best_mn[0]
            fbk_div             = best_mn[1]
            o_div               = {}
            if(frac_n_ssc_en):
                n_div           = best_mn[1]
                en_clk_list     = list(mno_dict[m_div][n_div].keys())
                cko_list        = en_clk_list
                idx_div_o       = 0
            else:
                n_div           = fbk_m_dict[fbk_div][m_div][0]
                en_clk_list     = [ck for ck in mno_dict[m_div][n_div]]
                cko_list        = [ck for ck in en_clk_list if(ck != fbk_name)]
                o_div[fbk_name] = fbk_m_dict[fbk_div][m_div][1]
                idx_div_o       = mno_dict[m_div][n_div][fbk_name].index(o_div[fbk_name])

            for ck in cko_list:
                o_div[ck]       = mno_dict[m_div][n_div][ck][idx_div_o]

            self.min_bw_factor  = gui_refclk_freq/m_div/best_bw_3db

            if(frac_n_ssc_en):
                div_ratio       = m_div/n_div
            else:
                div_ratio       = m_div/(n_div*o_div[fbk_name])

            self.ref_count      = self.get_ref_count_value(div_ratio)

            best_param          = {'M_DIV':m_div,
                                   'N_DIV':n_div,
                                   'O_DIV':o_div,
                                   'BWFAC':self.min_bw_factor}

            best_param.update(dict(best_resp_dict[fbk_div]['PARAM']))
            best_param.update(self.valid_response[best_resp_dict[fbk_div]['PARAM']])

            self.analog_param['ipp_ctrl'    ]       = '0b'+bin(dict(best_resp_dict[fbk_div]['PARAM'])['ipp_ctrl'    ])[2:].rjust(4,'0')
            self.analog_param['bw_ctrl_bias']       = '0b'+bin(dict(best_resp_dict[fbk_div]['PARAM'])['bw_ctrl_bias'])[2:].rjust(4,'0')
            self.analog_param['ipp_sel'     ]       = '0b'+bin(dict(best_resp_dict[fbk_div]['PARAM'])['ipp_sel'     ])[2:].rjust(4,'0')
            self.analog_param['ipi_cmp'     ]       = '0b'+bin(dict(best_resp_dict[fbk_div]['PARAM'])['ipi_cmp'     ])[2:].rjust(4,'0')
            self.analog_param['cset'        ]       = str(dict(best_resp_dict[fbk_div]['PARAM'])['cset'        ])+'P'
            self.analog_param['cripple'     ]       = str(dict(best_resp_dict[fbk_div]['PARAM'])['cripple'     ])+'P'
            if(dict(best_resp_dict[fbk_div]['PARAM'])['v2i_pp_res'] % 1):
                self.analog_param['v2i_pp_res'  ]   = str(dict(best_resp_dict[fbk_div]['PARAM'])['v2i_pp_res'  ]).replace('.','P')+'K'
            else:
                self.analog_param['v2i_pp_res'  ]   = str(dict(best_resp_dict[fbk_div]['PARAM'])['v2i_pp_res'  ]).replace('.0','K')

            # -----------------------------
            # Update GUI attributes
            # -----------------------------
            gui_phasedet_freq                       = gui_refclk_freq/m_div
            if(frac_n_ssc_en):
                gui_vco_freq                        = gui_phasedet_freq*n_div
            else:
                gui_vco_freq                        = gui_phasedet_freq*n_div*o_div[fbk_name]

            self.gui_m_div.cal_val                  = m_div
            self.gui_n_div.cal_val                  = n_div
            self.gui_frac_n_div.cal_val             = round((n_div % 1) * self.FRAC_N_MAX1)
            self.gui_phasedet_freq.cal_val          = gui_phasedet_freq
            self.gui_vco_freq.cal_val               = gui_vco_freq

            for ck in en_clk_list:
                self.gui_clkout[ck]['DIV'].cal_val  = o_div[ck]
                self.gui_clkout[ck]['FREQ'].cal_val = gui_vco_freq/o_div[ck]

        self.rtl_params = self.set_rtl_params()
        return best_param

    def set_rtl_params(self):
        global  INTFBKDEL_SEL, PMU_WAITFORLOCK, REF_OSC_CTRL, REF_COUNTS, EN_REFCLK_MON, \
                FVCO, FVCO_STR, CLKI_FREQ, CLKI_FREQ_STR, CLKI_DIVIDER_ACTUAL_STR, FRAC_N_EN, FBK_MODE, \
                FBCLK_DIVIDER_ACTUAL_STR, SSC_N_CODE_STR, SSC_F_CODE_STR, \
                SS_EN, SSC_PROFILE, SSC_TBASE_STR, SSC_STEP_IN_STR, SSC_REG_WEIGHTING_SEL_STR, \
                PLL_REFCLK_FROM_PIN, IO_TYPE, DYN_PORTS_EN, PLL_RST, LOCK_EN, \
                PLL_LOCK_STICKY, LMMI_EN, APB_EN, APB_SOFT_REG_EN, LEGACY_EN, POWERDOWN_EN, \
                IPI_CMP, CSET, CRIPPLE, IPP_CTRL, IPP_SEL, BW_CTL_BIAS, \
                V2I_PP_RES, KP_VCO, V2I_KVCO_SEL, V2I_1V_EN, \
                           CLKOP_BYPASS,  ENCLKOP_EN,  CLKOP_FREQ_ACTUAL,  DIVOP_ACTUAL_STR,  CLKOP_PHASE_ACTUAL,  DELA, PHIA, TRIM_EN_P, CLKOP_TRIM_MODE, CLKOP_TRIM, \
                CLKOS_EN,  CLKOS_BYPASS,  ENCLKOS_EN,  CLKOS_FREQ_ACTUAL,  DIVOS_ACTUAL_STR,  CLKOS_PHASE_ACTUAL,  DELB, PHIB, TRIM_EN_S, CLKOS_TRIM_MODE, CLKOS_TRIM, \
                CLKOS2_EN, CLKOS2_BYPASS, ENCLKOS2_EN, CLKOS2_FREQ_ACTUAL, DIVOS2_ACTUAL_STR, CLKOS2_PHASE_ACTUAL, DELC, PHIC, \
                CLKOS3_EN, CLKOS3_BYPASS, ENCLKOS3_EN, CLKOS3_FREQ_ACTUAL, DIVOS3_ACTUAL_STR, CLKOS3_PHASE_ACTUAL, DELD, PHID, \
                CLKOS4_EN, CLKOS4_BYPASS, ENCLKOS4_EN, CLKOS4_FREQ_ACTUAL, DIVOS4_ACTUAL_STR, CLKOS4_PHASE_ACTUAL, DELE, PHIE, \
                CLKOS5_EN, CLKOS5_BYPASS, ENCLKOS5_EN, CLKOS5_FREQ_ACTUAL, DIVOS5_ACTUAL_STR, CLKOS5_PHASE_ACTUAL, DELF, PHIF

        rtl_params                                  = {}

        rtl_params['INTFBKDEL_SEL']                 = 'ENABLED' if(self.gui_en_int_fbkdel_sel.usr_val) else 'DISABLED'

        rtl_params['PMU_WAITFORLOCK']               = 'ENABLED' if(self.gui_en_pmu_wait_lock.usr_val) else 'DISABLED'
        rtl_params['EN_REFCLK_MON']                 = 1 if(self.gui_en_refclk_mon.usr_val) else 0
        rtl_params['REF_OSC_CTRL']                  = self.gui_refclk_mon_freq.usr_val if(self.gui_refclk_mon_freq.editopt) else \
                                                      self.gui_refclk_mon_freq.cal_val
        rtl_params['REF_COUNTS']                    = bin(self.ref_count)[2:].rjust(4,'0') if(self.gui_en_refclk_mon.usr_val) else '0000'

        rtl_params['FVCO']                          = self.gui_vco_freq.cal_val
        rtl_params['FVCO_STR']                      = str(self.gui_vco_freq.cal_val)
        rtl_params['CLKI_FREQ']                     = self.gui_refclk_freq.usr_val
        rtl_params['CLKI_FREQ_STR']                 = str(self.gui_refclk_freq.usr_val)
        rtl_params['CLKI_DIVIDER_ACTUAL_STR']       = str(self.gui_m_div.usr_val) if(self.gui_m_div.editopt) else \
                                                      str(self.gui_m_div.cal_val)

        gui_en_frac_n                               = self.gui_en_frac_n.usr_val
        rtl_params['FRAC_N_EN']                     = 1 if(gui_en_frac_n) else 0
        gui_en_usr_fbk                              = self.gui_en_usr_fbk.usr_val if(self.gui_en_usr_fbk.editopt) else \
                                                      self.gui_en_usr_fbk.cal_val
        gui_fbk_mode                                = self.gui_fbk_mode.usr_val if(self.gui_fbk_mode.editopt) else \
                                                      self.gui_fbk_mode.cal_val
        rtl_params['FBK_MODE']                      = 'USERFBCLK' if(gui_en_usr_fbk) else gui_fbk_mode
        gui_n_div                                   = self.gui_n_div.usr_val if(self.gui_n_div.editopt) else \
                                                      self.gui_n_div.cal_val
        rtl_params['FBCLK_DIVIDER_ACTUAL_STR']      = str(int(gui_n_div))
        rtl_params['SSC_N_CODE_STR']                = '0b'+bin(int(gui_n_div))[2:].rjust(9,'0')
        gui_frac_n_div                              = self.gui_frac_n_div.usr_val if(self.gui_frac_n_div.editopt) else \
                                                      self.gui_frac_n_div.cal_val
        rtl_params['SSC_F_CODE_STR']                = '0b'+bin(gui_frac_n_div)[2:].rjust(12,'0')+'000'

        gui_en_ssc                                  = self.gui_en_ssc.usr_val
        rtl_params['SS_EN']                         = 1 if(gui_en_ssc) else 0
        ssc_mod_freq                                = self.gui_ssc_mod_freq.usr_val if(self.gui_ssc_mod_freq.editopt) else \
                                                      self.gui_ssc_mod_freq.cal_val
        ssc_triangle                                = self.gui_ssc_mod_depth.usr_val if(self.gui_ssc_mod_depth.editopt) else \
                                                      self.gui_ssc_mod_depth.cal_val
        ssc_profile                                 = self.gui_ssc_profile.usr_val if(self.gui_ssc_profile.editopt) else \
                                                      self.gui_ssc_profile.cal_val
        (ssc_tbase,ssc_step_in,ssc_weight_sel)      = self.calc_ssc_parameters(gui_en_ssc,self.gui_phasedet_freq.cal_val,
                                                                               ssc_mod_freq,ssc_triangle,ssc_profile,gui_n_div)
        rtl_params['SSC_PROFILE']                   = ssc_profile
        rtl_params['SSC_TBASE_STR']                 = '0b'+bin(ssc_tbase)[2:].rjust(12,'0')
        rtl_params['SSC_STEP_IN_STR']               = '0b'+bin(ssc_step_in)[2:].rjust(7,'0')
        rtl_params['SSC_REG_WEIGHTING_SEL_STR']     = '0b'+bin(ssc_weight_sel)[2:].rjust(3,'0')

        clk_del                                     = ['DELA','DELB','DELC','DELD','DELE','DELF']
        clk_phi                                     = ['PHIA','PHIB','PHIC','PHID','PHIE','PHIF']
        for ck in self.gui_clkout:
            clk_enable                              = self.gui_clkout[ck]['EN'].usr_val if(self.gui_clkout[ck]['EN'].editopt) else \
                                                      self.gui_clkout[ck]['EN'].cal_val
            rtl_params[ck+'_EN']                    = 1 if(clk_enable) else 0

            clk_bypass                              = self.gui_clkout[ck]['BYP'].usr_val if(self.gui_clkout[ck]['BYP'].editopt) else \
                                                      self.gui_clkout[ck]['BYP'].cal_val
            rtl_params[ck+'_BYPASS']                = 1 if(clk_bypass) else 0

            clk_clken                               = self.gui_clkout[ck]['CLKEN'].usr_val if(self.gui_clkout[ck]['CLKEN'].editopt) else \
                                                      self.gui_clkout[ck]['CLKEN'].cal_val
            rtl_params['EN'+ck+'_EN']               = 1 if(clk_clken) else 0

            rtl_params[ck+'_FREQ_ACTUAL']           = self.gui_clkout[ck]['FREQ'].cal_val

            div_name                                = 'DIV'+ck.replace('CLK','')+'_ACTUAL_STR'
            div_minus1                              = int(self.gui_clkout[ck]['DIV'].cal_val-1)
            rtl_params[div_name]                    = str(div_minus1)


            cko_phase                               = self.gui_clkout[ck]['PHASE'].usr_val if(self.gui_clkout[ck]['PHASE'].editopt) else \
                                                      self.gui_clkout[ck]['PHASE'].cal_val
            del_phi                                 = self.calc_del_phase_setting(div_out=self.gui_clkout[ck]['DIV'].cal_val,
                                                                                  phase_shift=cko_phase)
            rtl_params[ck+'_PHASE_ACTUAL']          = cko_phase
            rtl_params[clk_del[self.clk_idx[ck]]]   = str(del_phi['DEL'])
            rtl_params[clk_phi[self.clk_idx[ck]]]   = str(del_phi['PHI'])

            if(ck == 'CLKOP' or ck == 'CLKOS'):
                trim_en_name                        = 'TRIM_EN_P' if(ck == 'CLKOP') else 'TRIM_EN_S'
                trim_en                             = self.gui_clkout[ck]['TRIM_EN'].usr_val if(self.gui_clkout[ck]['TRIM_EN'].editopt) else \
                                                      self.gui_clkout[ck]['TRIM_EN'].cal_val
                rtl_params[trim_en_name]            = 1 if(trim_en) else 0
                trim_mode                           = self.gui_clkout[ck]['TRIM_MODE'].usr_val if(self.gui_clkout[ck]['TRIM_MODE'].editopt) else \
                                                      self.gui_clkout[ck]['TRIM_MODE'].cal_val
                trim_mult                           = self.gui_clkout[ck]['TRIM_MULT'].usr_val if(self.gui_clkout[ck]['TRIM_MULT'].editopt) else \
                                                      self.gui_clkout[ck]['TRIM_MULT'].cal_val
                rtl_params[ck+'_TRIM_MODE']         = trim_mode
                rtl_params[ck+'_TRIM']              = self.calc_trim(trim_mode,trim_mult)


        rtl_params['PLL_REFCLK_FROM_PIN']           = 1 if(self.gui_en_refclk_pin.usr_val) else 0
        rtl_params['IO_TYPE']                       = self.gui_refclk_io_type.usr_val if(self.gui_refclk_io_type.editopt) else\
                                                      self.gui_refclk_io_type.cal_val
        rtl_params['DYN_PORTS_EN']                  = 1 if(self.gui_en_dyn_phase.usr_val) else 0
        rtl_params['PLL_RST']                       = 1 if(self.gui_en_pll_reset.usr_val) else 0
        rtl_params['LOCK_EN']                       = 1 if(self.gui_en_pll_lock.usr_val) else 0
        rtl_params['PLL_LOCK_STICKY']               = self.gui_pll_lock_sticky.usr_val if(self.gui_pll_lock_sticky.editopt) else \
                                                      self.gui_pll_lock_sticky.cal_val
        rtl_params['LMMI_EN']                       = 1 if(self.gui_reg_interface.usr_val == 'LMMI') else 0
        rtl_params['APB_EN']                        = 1 if(self.gui_reg_interface.usr_val == 'APB') else 0
        rtl_params['APB_SOFT_REG_EN']               = 1 if(self.gui_en_csr.get_val()) else 0
        rtl_params['LEGACY_EN']                     = 1 if(self.gui_en_legacy.usr_val) else 0
        rtl_params['POWERDOWN_EN']                  = 1 if(self.gui_en_powerdown.usr_val) else 0

        rtl_params['IPI_CMP']                       = self.analog_param['ipi_cmp']
        rtl_params['CSET']                          = self.analog_param['cset']
        rtl_params['CRIPPLE']                       = self.analog_param['cripple']
        rtl_params['IPP_CTRL']                      = self.analog_param['ipp_ctrl']
        rtl_params['IPP_SEL']                       = self.analog_param['ipp_sel']
        rtl_params['BW_CTL_BIAS']                   = self.analog_param['bw_ctrl_bias']
        rtl_params['V2I_PP_RES']                    = self.analog_param['v2i_pp_res']
        rtl_params['KP_VCO']                        = '0b00011' # if(VOLTAGE=1.0) else '0b11001'
        rtl_params['V2I_KVCO_SEL']                  = '60'      # if(VOLTAGE=1.0) else '85'
        rtl_params['V2I_1V_EN']                     = 'ENABLED' # if(VOLTAGE=1.0) else 'DISABLED'

        INTFBKDEL_SEL                               = rtl_params['INTFBKDEL_SEL']
        PMU_WAITFORLOCK                             = rtl_params['PMU_WAITFORLOCK']
        EN_REFCLK_MON                               = rtl_params['EN_REFCLK_MON']
        REF_OSC_CTRL                                = rtl_params['REF_OSC_CTRL']
        REF_COUNTS                                  = rtl_params['REF_COUNTS']
        FVCO                                        = rtl_params['FVCO']
        FVCO_STR                                    = rtl_params['FVCO_STR']
        CLKI_FREQ                                   = rtl_params['CLKI_FREQ']
        CLKI_FREQ_STR                               = rtl_params['CLKI_FREQ_STR']
        CLKI_DIVIDER_ACTUAL_STR                     = rtl_params['CLKI_DIVIDER_ACTUAL_STR']
        FRAC_N_EN                                   = rtl_params['FRAC_N_EN']
        FBK_MODE                                    = rtl_params['FBK_MODE']
        FBCLK_DIVIDER_ACTUAL_STR                    = rtl_params['FBCLK_DIVIDER_ACTUAL_STR']
        SSC_N_CODE_STR                              = rtl_params['SSC_N_CODE_STR']
        SSC_F_CODE_STR                              = rtl_params['SSC_F_CODE_STR']
        SS_EN                                       = rtl_params['SS_EN']
        SSC_PROFILE                                 = rtl_params['SSC_PROFILE']
        SSC_TBASE_STR                               = rtl_params['SSC_TBASE_STR']
        SSC_STEP_IN_STR                             = rtl_params['SSC_STEP_IN_STR']
        SSC_REG_WEIGHTING_SEL_STR                   = rtl_params['SSC_REG_WEIGHTING_SEL_STR']
        PLL_REFCLK_FROM_PIN                         = rtl_params['PLL_REFCLK_FROM_PIN']
        IO_TYPE                                     = rtl_params['IO_TYPE']
        DYN_PORTS_EN                                = rtl_params['DYN_PORTS_EN']
        PLL_RST                                     = rtl_params['PLL_RST']
        LOCK_EN                                     = rtl_params['LOCK_EN']
        PLL_LOCK_STICKY                             = rtl_params['PLL_LOCK_STICKY']
        LMMI_EN                                     = rtl_params['LMMI_EN']
        APB_EN                                      = rtl_params['APB_EN']
        APB_SOFT_REG_EN                             = rtl_params['APB_SOFT_REG_EN']
        LEGACY_EN                                   = rtl_params['LEGACY_EN']
        POWERDOWN_EN                                = rtl_params['POWERDOWN_EN']
        IPI_CMP                                     = rtl_params['IPI_CMP']
        CSET                                        = rtl_params['CSET']
        CRIPPLE                                     = rtl_params['CRIPPLE']
        IPP_CTRL                                    = rtl_params['IPP_CTRL']
        IPP_SEL                                     = rtl_params['IPP_SEL']
        BW_CTL_BIAS                                 = rtl_params['BW_CTL_BIAS']
        V2I_PP_RES                                  = rtl_params['V2I_PP_RES']
        KP_VCO                                      = rtl_params['KP_VCO']
        V2I_KVCO_SEL                                = rtl_params['V2I_KVCO_SEL']
        V2I_1V_EN                                   = rtl_params['V2I_1V_EN']
        CLKOP_BYPASS                                = rtl_params['CLKOP_BYPASS']
        ENCLKOP_EN                                  = rtl_params['ENCLKOP_EN']
        CLKOP_FREQ_ACTUAL                           = rtl_params['CLKOP_FREQ_ACTUAL']
        DIVOP_ACTUAL_STR                            = rtl_params['DIVOP_ACTUAL_STR']
        CLKOP_PHASE_ACTUAL                          = rtl_params['CLKOP_PHASE_ACTUAL']
        DELA                                        = rtl_params['DELA']
        PHIA                                        = rtl_params['PHIA']
        TRIM_EN_P                                   = rtl_params['TRIM_EN_P']
        CLKOP_TRIM_MODE                             = rtl_params['CLKOP_TRIM_MODE']
        CLKOP_TRIM                                  = rtl_params['CLKOP_TRIM']
        CLKOS_EN                                    = rtl_params['CLKOS_EN']
        CLKOS_BYPASS                                = rtl_params['CLKOS_BYPASS']
        ENCLKOS_EN                                  = rtl_params['ENCLKOS_EN']
        CLKOS_FREQ_ACTUAL                           = rtl_params['CLKOS_FREQ_ACTUAL']
        DIVOS_ACTUAL_STR                            = rtl_params['DIVOS_ACTUAL_STR']
        CLKOS_PHASE_ACTUAL                          = rtl_params['CLKOS_PHASE_ACTUAL']
        DELB                                        = rtl_params['DELB']
        PHIB                                        = rtl_params['PHIB']
        TRIM_EN_S                                   = rtl_params['TRIM_EN_S']
        CLKOS_TRIM_MODE                             = rtl_params['CLKOS_TRIM_MODE']
        CLKOS_TRIM                                  = rtl_params['CLKOS_TRIM']
        CLKOS2_EN                                   = rtl_params['CLKOS2_EN']
        CLKOS2_BYPASS                               = rtl_params['CLKOS2_BYPASS']
        ENCLKOS2_EN                                 = rtl_params['ENCLKOS2_EN']
        CLKOS2_FREQ_ACTUAL                          = rtl_params['CLKOS2_FREQ_ACTUAL']
        DIVOS2_ACTUAL_STR                           = rtl_params['DIVOS2_ACTUAL_STR']
        CLKOS2_PHASE_ACTUAL                         = rtl_params['CLKOS2_PHASE_ACTUAL']
        DELC                                        = rtl_params['DELC']
        PHIC                                        = rtl_params['PHIC']
        CLKOS3_EN                                   = rtl_params['CLKOS3_EN']
        CLKOS3_BYPASS                               = rtl_params['CLKOS3_BYPASS']
        ENCLKOS3_EN                                 = rtl_params['ENCLKOS3_EN']
        CLKOS3_FREQ_ACTUAL                          = rtl_params['CLKOS3_FREQ_ACTUAL']
        DIVOS3_ACTUAL_STR                           = rtl_params['DIVOS3_ACTUAL_STR']
        CLKOS3_PHASE_ACTUAL                         = rtl_params['CLKOS3_PHASE_ACTUAL']
        DELD                                        = rtl_params['DELD']
        PHID                                        = rtl_params['PHID']
        CLKOS4_EN                                   = rtl_params['CLKOS4_EN']
        CLKOS4_BYPASS                               = rtl_params['CLKOS4_BYPASS']
        ENCLKOS4_EN                                 = rtl_params['ENCLKOS4_EN']
        CLKOS4_FREQ_ACTUAL                          = rtl_params['CLKOS4_FREQ_ACTUAL']
        DIVOS4_ACTUAL_STR                           = rtl_params['DIVOS4_ACTUAL_STR']
        CLKOS4_PHASE_ACTUAL                         = rtl_params['CLKOS4_PHASE_ACTUAL']
        DELE                                        = rtl_params['DELE']
        PHIE                                        = rtl_params['PHIE']
        CLKOS5_EN                                   = rtl_params['CLKOS5_EN']
        CLKOS5_BYPASS                               = rtl_params['CLKOS5_BYPASS']
        ENCLKOS5_EN                                 = rtl_params['ENCLKOS5_EN']
        CLKOS5_FREQ_ACTUAL                          = rtl_params['CLKOS5_FREQ_ACTUAL']
        DIVOS5_ACTUAL_STR                           = rtl_params['DIVOS5_ACTUAL_STR']
        CLKOS5_PHASE_ACTUAL                         = rtl_params['CLKOS5_PHASE_ACTUAL']
        DELF                                        = rtl_params['DELF']
        PHIF                                        = rtl_params['PHIF']

        return rtl_params
    # end def set_rtl_params

    def update_gui_display(self, best_param):
        global gui_m_div_disp,gui_n_div_disp, \
               gui_vco_freq, gui_phasedet_freq, \
               gui_frac_n_div_disp,fbclk_divider_decimal_disp, \
               gui_clk_op_freq_disp,gui_clk_op_div_disp, \
               gui_clk_os_freq_disp,gui_clk_os_div_disp, \
               gui_clk_s2_freq_disp,gui_clk_s2_div_disp, \
               gui_clk_s3_freq_disp,gui_clk_s3_div_disp, \
               gui_clk_s4_freq_disp,gui_clk_s4_div_disp, \
               gui_clk_s5_freq_disp,gui_clk_s5_div_disp

        gui_m_div_disp                          = best_param['M_DIV']
        gui_phasedet_freq                       = self.gui_refclk_freq.usr_val/gui_m_div_disp

        fbclk_divider_decimal_disp              = best_param['N_DIV']
        gui_n_div_disp                          = int(best_param['N_DIV'])
        gui_frac_n_div_disp                     = round((best_param['N_DIV'] % 1) * self.FRAC_N_MAX1)

        fbk_name                                = self.gui_fbk_mode.usr_val if(self.gui_fbk_mode.editopt) else \
                                                  self.gui_fbk_mode.cal_val
        fbk_name                                = fbk_name.replace('INT','')
        if(self.gui_en_frac_n.usr_val or self.gui_en_ssc.usr_val):
            gui_vco_freq                        = fbclk_divider_decimal_disp*gui_phasedet_freq
        else:
            gui_vco_freq                        = best_param['O_DIV'][fbk_name]*fbclk_divider_decimal_disp*gui_phasedet_freq

        if('CLKOP' in best_param['O_DIV']):
            gui_clk_op_div_disp                 = best_param['O_DIV']['CLKOP']
            gui_clk_op_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOP']
        if('CLKOS' in best_param['O_DIV']):
            gui_clk_os_div_disp                 = best_param['O_DIV']['CLKOS']
            gui_clk_os_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOS']
        if('CLKOS2' in best_param['O_DIV']):
            gui_clk_s2_div_disp                 = best_param['O_DIV']['CLKOS2']
            gui_clk_s2_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOS2']
        if('CLKOS3' in best_param['O_DIV']):
            gui_clk_s3_div_disp                 = best_param['O_DIV']['CLKOS3']
            gui_clk_s3_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOS3']
        if('CLKOS4' in best_param['O_DIV']):
            gui_clk_s4_div_disp                 = best_param['O_DIV']['CLKOS4']
            gui_clk_s4_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOS4']
        if('CLKOS5' in best_param['O_DIV']):
            gui_clk_s5_div_disp                 = best_param['O_DIV']['CLKOS5']
            gui_clk_s5_freq_disp                = gui_vco_freq/best_param['O_DIV']['CLKOS5']

    # def update_gui_display

    def write_to_cfgfile(self,fh,var_name,d_typ=0,clk_idx=0,clk_attr='FREQ', ckvar='gui_clk_op_freq'):
        # d_typ: 0 - write as it is
        #        1 - bool
        #        2 - need string qoute
        sub_idx                                             = '[clk_idx][clk_attr].' if(var_name == 'gui_clkout') else '.'
        if(eval('self.'+var_name+sub_idx+'editopt')):
            value                                           = eval('self.'+var_name+sub_idx+'usr_val')
            usr_val                                         = str(bool(value)).lower() if(d_typ == 1) else value
            act_var_name                                    = ckvar if(var_name == 'gui_clkout') else var_name
            if(d_typ == 2):
                fh.write(' "{}" : "{}",\n'.format(act_var_name,usr_val))
            else:
                fh.write(' "{}" : {},\n'.format(act_var_name,usr_val))

    def gen_cfg_file(self):
        import os

        ip_inst_name                                        = runtime_info.ip_inst_name
        ip_inst_dir                                         = runtime_info.ip_inst_dir
        ip_cfg_file                                         = os.path.realpath(os.path.join(ip_inst_dir,ip_inst_name+'_cfg_file.cfg'))
        print("DEBUG: ip_cfg_file = ",ip_cfg_file)

        try:
            fh = open(ip_cfg_file,'w')
        except OSError as err:
            print("OS error: {}".format(err))

        fh.write('{'+'\n')

        # User configurable settings
        # {var_name : d_typ}
        var_name_list = [('gui_config_mode'       , 2), ('gui_en_frac_n'     , 1), ('gui_en_ssc'       , 1), ('gui_en_usr_fbk'    , 1)
                        ,('gui_en_int_fbkdel_sel' , 1), ('gui_refclk_freq'   , 0), ('gui_m_div'        , 0), ('gui_en_refclk_mon' , 1)
                        ,('gui_refclk_mon_freq'   , 2), ('gui_fbk_mode'      , 2), ('gui_n_div'        , 0), ('gui_frac_n_div'    , 0)
                        ,('gui_ssc_profile'       , 2), ('gui_ssc_mod_depth' , 0), ('gui_ssc_mod_freq' , 0), ('gui_en_refclk_pin' , 1)
                        ,('gui_refclk_io_type'    , 2), ('gui_en_dyn_phase'  , 1), ('gui_en_pll_reset' , 1), ('gui_en_pll_lock'   , 1)
                        ,('gui_pll_lock_sticky'   , 1), ('gui_reg_interface' , 2), ('gui_en_csr'       , 1), ('gui_en_legacy'     , 1)
                        ,('gui_en_powerdown'      , 1), ('gui_clkout'        , 0)
                         ]

        ckvar_name = {'CLKOP':'clk_op','CLKOS':'clk_os','CLKOS2':'clk_s2','CLKOS3':'clk_s3','CLKOS4':'clk_s4','CLKOS5':'clk_s5'}
        for var_name,d_typ in var_name_list:
            #print("***DEBUG*** var_name={}, d_typ={}".format(var_name,d_typ))
            if(var_name == 'gui_clkout'):
                for ck in self.gui_clkout:
                    if(ck != 'CLKOP'):
                        self.write_to_cfgfile(fh,var_name,1,ck,'EN','gui_'+str(ckvar_name[ck])+'_'+'en')

                    self.write_to_cfgfile(fh,var_name,1,ck,'BYP','gui_'+str(ckvar_name[ck])+'_'+'byp')
                    self.write_to_cfgfile(fh,var_name,1,ck,'CLKEN','gui_en_clken_'+str(ckvar_name[ck]).replace('clk_',''))
                    self.write_to_cfgfile(fh,var_name,0,ck,'FREQ','gui_'+str(ckvar_name[ck])+'_'+'freq')
                    self.write_to_cfgfile(fh,var_name,0,ck,'DIV','gui_'+str(ckvar_name[ck])+'_'+'div')
                    self.write_to_cfgfile(fh,var_name,0,ck,'PHASE','gui_'+str(ckvar_name[ck])+'_'+'phase')
                    self.write_to_cfgfile(fh,var_name,0,ck,'TOL','gui_'+str(ckvar_name[ck])+'_'+'tol')

                    if(ck == 'CLKOP' or ck == 'CLKOS'):
                        self.write_to_cfgfile(fh,var_name,1,ck,'TRIM_EN','gui_'+str(ckvar_name[ck])+'_'+'trim_en')
                        self.write_to_cfgfile(fh,var_name,2,ck,'TRIM_MODE','gui_'+str(ckvar_name[ck])+'_'+'trim_mode')
                        self.write_to_cfgfile(fh,var_name,0,ck,'TRIM_MULT','gui_'+str(ckvar_name[ck])+'_'+'trim_mult')
            else:
                self.write_to_cfgfile(fh,var_name,d_typ)

        global gui_sim_type
        fh.write(' "gui_sim_type" : {}\n'.format(gui_sim_type))
        fh.write('}'+'\n')
        fh.close()

        return 0

    def cmd_run_calc(self):
        print("[DEBUG] bypass_bw_factor = ",self.bypass_bw_factor)

        if(self.all_clkout_dis_or_byp):
            best_param = {'M_DIV': 1,'N_DIV': 1,'O_DIV': {'CLKOP': 8},
                          'fbk_div': 8, 'm_div': 1,
                          'ipp_ctrl': 4, 'bw_ctrl_bias': 15, 'ipp_sel': 15,
                          'ipi_cmp': 4, 'cset': 24, 'v2i_pp_res': 9.0, 'cripple': 3,
                          'PEAK': 1.3481176682179599, 'BW_3DB': 7.673614893618202,
                          'BW_OPL': 4.731512589614814, 'PM_3DB': 51.16659648567364}

            msg0 = ""
            msg0 = ("%s[INFO] All clocks are disabled/bypassed!\n\n" % (msg0))
            print(msg0)
        else:
            start      = self.perf_counter()
            best_param = self.get_final_param()
            end        = self.perf_counter()
            print("[DEBUG] Total process time : ",end-start)

        if(len(best_param)):
            self.update_gui_display(best_param)
            self.gen_cfg_file()
            #print("[DEBUG] mno_dict = {}".format(self.mno_dict))

            msg0 = ""
            msg1 = "\n"
            if(self.bypass_bw_factor):
                msg0 = ("%s[WARNING] BW_FACTOR requirement is bypassed!\n\n" % (msg0))

            msg0 = ("%s[INFO] Done Parameter Optimization.\n" % (msg0))
            msg1 = ("%sBest Param : %s\n" % (msg0,best_param ))
            msg1 = ("%s\n Analog Parameters : \n"   % (msg1))
            msg1 = ("%s - CSET        \t: %s\t\t - CRIPPLE     \t: %s\t\t - IPI_CMP     \t: %s\n" % (msg1,self.rtl_params['CSET'],self.rtl_params['CRIPPLE'],self.rtl_params['IPI_CMP']))
            msg1 = ("%s - V2I_PP_RES  \t: %s\t\t - IPP_SEL     \t: %s\t\t -             \t    \n" % (msg1,self.rtl_params['V2I_PP_RES'],self.rtl_params['IPP_SEL']))
            msg1 = ("%s - IPP_CTRL    \t: %s\t\t - BW_CTL_BIAS   : %s\t\t -             \t    \n" % (msg1,self.rtl_params['IPP_CTRL'],self.rtl_params['BW_CTL_BIAS']))

            print(msg1)
            PluginUtil.post_info("%s" % (msg0))
        else:
            msg0 = ""
            if(self.mno_dict):
                #self.bypass_bw_factor = 1
                msg0 = ("%s[ERROR] Unable to find valid Analog Parameter combination.\n" % (msg0))
                msg0 = ("%s        ***Change the input settings.\n" % (msg0))
            else:
                msg0 = ("%s[ERROR] No valid dividers found!\n" % (msg0))

            PluginUtil.post_error("%s" % (msg0))

        return

# end class GPLL_PARAM

# ----------------------
# GPLL_PARAM instance
# ----------------------
gpll_param = GPLL_PARAM()

# -----------------------------------------------------------------------------------
# Check if the device is a JP device. Return True if it is JP device, False otherwise
# -----------------------------------------------------------------------------------
def check_is_jp_device():
    device = runtime_info.device_info.device(1)
    #print("DEBUG: device = ",device)
    return device.lower().endswith('p')