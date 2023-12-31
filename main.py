"""
CONNECTIONS

GP3 : scl
gp2 : sda
GP4 : UART1 TX
GP5 : UART1 RX

WIDGETS

j0 : progress bar -> j0.val=20
h0 : vertical slider -> get h0.val

"""

import utime as time

_REGISTER_MASK = const(0x03)
_REGISTER_CONVERT = const(0x00)
_REGISTER_CONFIG = const(0x01)
_REGISTER_LOWTHRESH = const(0x02)
_REGISTER_HITHRESH = const(0x03)

_OS_MASK = const(0x8000)
_OS_SINGLE = const(0x8000)  # Write: Set to start a single-conversion
_OS_BUSY = const(0x0000)  # Read: Bit=0 when conversion is in progress
_OS_NOTBUSY = const(0x8000)  # Read: Bit=1 when no conversion is in progress

_MUX_MASK = const(0x7000)
_MUX_DIFF_0_1 = const(0x0000)  # Differential P  =  AIN0, N  =  AIN1 (default)
_MUX_DIFF_0_3 = const(0x1000)  # Differential P  =  AIN0, N  =  AIN3
_MUX_DIFF_1_3 = const(0x2000)  # Differential P  =  AIN1, N  =  AIN3
_MUX_DIFF_2_3 = const(0x3000)  # Differential P  =  AIN2, N  =  AIN3
_MUX_SINGLE_0 = const(0x4000)  # Single-ended AIN0
_MUX_SINGLE_1 = const(0x5000)  # Single-ended AIN1
_MUX_SINGLE_2 = const(0x6000)  # Single-ended AIN2
_MUX_SINGLE_3 = const(0x7000)  # Single-ended AIN3

_PGA_MASK = const(0x0E00)
_PGA_6_144V = const(0x0000)  # +/-6.144V range  =  Gain 2/3
_PGA_4_096V = const(0x0200)  # +/-4.096V range  =  Gain 1
_PGA_2_048V = const(0x0400)  # +/-2.048V range  =  Gain 2 (default)
_PGA_1_024V = const(0x0600)  # +/-1.024V range  =  Gain 4
_PGA_0_512V = const(0x0800)  # +/-0.512V range  =  Gain 8
_PGA_0_256V = const(0x0A00)  # +/-0.256V range  =  Gain 16

_MODE_MASK = const(0x0100)
_MODE_CONTIN = const(0x0000)  # Continuous conversion mode
_MODE_SINGLE = const(0x0100)  # Power-down single-shot mode (default)

_DR_MASK = const(0x00E0)     # Values ADS1015/ADS1115
_DR_128SPS = const(0x0000)   # 128 /8 samples per second
_DR_250SPS = const(0x0020)   # 250 /16 samples per second
_DR_490SPS = const(0x0040)   # 490 /32 samples per second
_DR_920SPS = const(0x0060)   # 920 /64 samples per second
_DR_1600SPS = const(0x0080)  # 1600/128 samples per second (default)
_DR_2400SPS = const(0x00A0)  # 2400/250 samples per second
_DR_3300SPS = const(0x00C0)  # 3300/475 samples per second
_DR_860SPS = const(0x00E0)  # -   /860 samples per Second

_CMODE_MASK = const(0x0010)
_CMODE_TRAD = const(0x0000)  # Traditional comparator with hysteresis (default)
_CMODE_WINDOW = const(0x0010)  # Window comparator

_CPOL_MASK = const(0x0008)
_CPOL_ACTVLOW = const(0x0000)  # ALERT/RDY pin is low when active (default)
_CPOL_ACTVHI = const(0x0008)  # ALERT/RDY pin is high when active

_CLAT_MASK = const(0x0004)  # Determines if ALERT/RDY pin latches once asserted
_CLAT_NONLAT = const(0x0000)  # Non-latching comparator (default)
_CLAT_LATCH = const(0x0004)  # Latching comparator

_CQUE_MASK = const(0x0003)
_CQUE_1CONV = const(0x0000)  # Assert ALERT/RDY after one conversions
_CQUE_2CONV = const(0x0001)  # Assert ALERT/RDY after two conversions
_CQUE_4CONV = const(0x0002)  # Assert ALERT/RDY after four conversions
# Disable the comparator and put ALERT/RDY in high state (default)
_CQUE_NONE = const(0x0003)

_GAINS = (
    _PGA_6_144V,  # 2/3x
    _PGA_4_096V,  # 1x
    _PGA_2_048V,  # 2x
    _PGA_1_024V,  # 4x
    _PGA_0_512V,  # 8x
    _PGA_0_256V   # 16x
)

_GAINS_V = (
    6.144,  # 2/3x
    4.096,  # 1x
    2.048,  # 2x
    1.024,  # 4x
    0.512,  # 8x
    0.256  # 16x
)

_CHANNELS = {
    (0, None): _MUX_SINGLE_0,
    (1, None): _MUX_SINGLE_1,
    (2, None): _MUX_SINGLE_2,
    (3, None): _MUX_SINGLE_3,
    (0, 1): _MUX_DIFF_0_1,
    (0, 3): _MUX_DIFF_0_3,
    (1, 3): _MUX_DIFF_1_3,
    (2, 3): _MUX_DIFF_2_3,
}

_RATES = (
    _DR_128SPS,   # 128/8 samples per second
    _DR_250SPS,   # 250/16 samples per second
    _DR_490SPS,   # 490/32 samples per second
    _DR_920SPS,   # 920/64 samples per second
    _DR_1600SPS,  # 1600/128 samples per second (default)
    _DR_2400SPS,  # 2400/250 samples per second
    _DR_3300SPS,  # 3300/475 samples per second
    _DR_860SPS    # - /860 samples per Second
)


class ADS1115:
    def __init__(self, i2c, address=0x48, gain=1):
        self.i2c = i2c
        self.address = address
        self.gain = gain
        self.temp2 = bytearray(2)

    def _write_register(self, register, value):
        self.temp2[0] = value >> 8
        self.temp2[1] = value & 0xff
        self.i2c.writeto_mem(self.address, register, self.temp2)

    def _read_register(self, register):
        self.i2c.readfrom_mem_into(self.address, register, self.temp2)
        return (self.temp2[0] << 8) | self.temp2[1]

    def raw_to_v(self, raw):
        v_p_b = _GAINS_V[self.gain] / 32767
        return raw * v_p_b

    def set_conv(self, rate=4, channel1=0, channel2=None):
        """Set mode for read_rev"""
        self.mode = (_CQUE_NONE | _CLAT_NONLAT |
                     _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                     _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] |
                     _CHANNELS[(channel1, channel2)])

    def read(self, rate=4, channel1=0, channel2=None):
        """Read voltage between a channel and GND.
           Time depends on conversion rate."""
        self._write_register(_REGISTER_CONFIG, (_CQUE_NONE | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_SINGLE | _OS_SINGLE | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)]))
        while not self._read_register(_REGISTER_CONFIG) & _OS_NOTBUSY:
            time.sleep_ms(1)
        res = self._read_register(_REGISTER_CONVERT)
        return res if res < 32768 else res - 65536

    def read_rev(self):
        """Read voltage between a channel and GND. and then start
           the next conversion."""
        res = self._read_register(_REGISTER_CONVERT)
        self._write_register(_REGISTER_CONFIG, self.mode)
        return res if res < 32768 else res - 65536

    def alert_start(self, rate=4, channel1=0, channel2=None,
                    threshold_high=0x4000, threshold_low=0, latched=False) :
        """Start continuous measurement, set ALERT pin on threshold."""
        self._write_register(_REGISTER_LOWTHRESH, threshold_low)
        self._write_register(_REGISTER_HITHRESH, threshold_high)
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV |
                             _CLAT_LATCH if latched else _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_CONTIN | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)])

    def conversion_start(self, rate=4, channel1=0, channel2=None):
        """Start continuous measurement, trigger on ALERT/RDY pin."""
        self._write_register(_REGISTER_LOWTHRESH, 0)
        self._write_register(_REGISTER_HITHRESH, 0x8000)
        self._write_register(_REGISTER_CONFIG, _CQUE_1CONV | _CLAT_NONLAT |
                             _CPOL_ACTVLOW | _CMODE_TRAD | _RATES[rate] |
                             _MODE_CONTIN | _GAINS[self.gain] |
                             _CHANNELS[(channel1, channel2)])

    def alert_read(self):
        """Get the last reading from the continuous measurement."""
        res = self._read_register(_REGISTER_CONVERT)
        return res if res < 32768 else res - 65536


from machine import Pin, UART, I2C
import time


class UI:
    IB2_16H_24H = b'e\x00\x01\x01\xff\xff\xff'
    IB2_16H_16H = b'e\x00\x02\x01\xff\xff\xff'
    UNIMOULD = b'e\x00\x06\x01\xff\xff\xff'
    
    UV_15M = b'e\x00\x05\x01\xff\xff\xff'
    UV_5M = b'e\x00\x04\x01\xff\xff\xff'
    UV_5M = b'e\x00\x03\x01\xff\xff\xff'
    
    OVEN_TEMP_TEXT = "t0"
    OVEN_TIME_LEFT_TEXT= "t1"
    
    def put_0_if_necessary(n):
        if n < 10:
            return "0"+str(n)
        else:
            return str(n)

def set_text(element, text):
    send(element+".txt=\""+text+"\"")

class Oven:
    
    N_MEASUREMENTS = 10
    
    # [(<duration in hour>,<temp in C°>), (...), ..]
    CYCLES = {
        UI.IB2_16H_24H: [(16, 0), (24, 40)],
        UI.IB2_16H_16H: [(16, 0), (16, 60)],
        # 10hrs at 60°C › 2hrs at 70°C › 2hrs at 80°C › 2hrs at 90°C
        UI.UNIMOULD: [(10, 60), (2, 70), (2, 80), (2, 90)]
    }
    
    def get_temp_from_voltage(self, v):
        li_0_100_every_0_1 = [0.000000, 0.003945, 0.007891, 0.011837, 0.015784, 0.019731, 0.023679, 0.027627, 0.031576, 0.035525, 0.039474, 0.043425, 0.047375, 0.051326, 0.055278, 0.059230, 0.063182, 0.067135, 0.071089, 0.075043, 0.078997, 0.082952, 0.086908, 0.090863, 0.094820, 0.098777, 0.102734, 0.106692, 0.110650, 0.114609, 0.118568, 0.122528, 0.126488, 0.130448, 0.134410, 0.138371, 0.142333, 0.146296, 0.150259, 0.154222, 0.158186, 0.162150, 0.166115, 0.170081, 0.174046, 0.178013, 0.181979, 0.185947, 0.189914, 0.193882, 0.197851, 0.201820, 0.205790, 0.209760, 0.213730, 0.217701, 0.221672, 0.225644, 0.229616, 0.233589, 0.237562, 0.241536, 0.245510, 0.249485, 0.253460, 0.257435, 0.261411, 0.265388, 0.269364, 0.273342, 0.277320, 0.281298, 0.285276, 0.289256, 0.293235, 0.297215, 0.301196, 0.305177, 0.309158, 0.313140, 0.317122, 0.321105, 0.325088, 0.329072, 0.333056, 0.337040, 0.341025, 0.345011, 0.348997, 0.352983, 0.356970, 0.360957, 0.364945, 0.368933, 0.372921, 0.376910, 0.380900, 0.384890, 0.388880, 0.392871, 0.396862, 0.400854, 0.404846, 0.408838, 0.412831, 0.416824, 0.420818, 0.424813, 0.428807, 0.432802, 0.436798, 0.440794, 0.444790, 0.448787, 0.452785, 0.456782, 0.460780, 0.464779, 0.468778, 0.472778, 0.476777, 0.480778, 0.484779, 0.488780, 0.492781, 0.496783, 0.500786, 0.504789, 0.508792, 0.512796, 0.516800, 0.520805, 0.524810, 0.528815, 0.532821, 0.536827, 0.540834, 0.544841, 0.548849, 0.552857, 0.556865, 0.560874, 0.564883, 0.568893, 0.572903, 0.576913, 0.580924, 0.584935, 0.588947, 0.592959, 0.596972, 0.600985, 0.604998, 0.609012, 0.613026, 0.617041, 0.621056, 0.625072, 0.629087, 0.633104, 0.637120, 0.641138, 0.645155, 0.649173, 0.653191, 0.657210, 0.661229, 0.665249, 0.669269, 0.673289, 0.677310, 0.681331, 0.685353, 0.689375, 0.693397, 0.697420, 0.701443, 0.705467, 0.709491, 0.713515, 0.717540, 0.721565, 0.725591, 0.729617, 0.733643, 0.737670, 0.741697, 0.745725, 0.749753, 0.753781, 0.757810, 0.761839, 0.765869, 0.769899, 0.773929, 0.777960, 0.781991, 0.786023, 0.790055, 0.794087, 0.798120, 0.802153, 0.806186, 0.810220, 0.814254, 0.818289, 0.822324, 0.826360, 0.830395, 0.834432, 0.838468, 0.842505, 0.846543, 0.850580, 0.854619, 0.858657, 0.862696, 0.866735, 0.870775, 0.874815, 0.878855, 0.882896, 0.886937, 0.890979, 0.895021, 0.899063, 0.903106, 0.907149, 0.911192, 0.915236, 0.919280, 0.923325, 0.927370, 0.931415, 0.935461, 0.939507, 0.943553, 0.947600, 0.951647, 0.955695, 0.959743, 0.963791, 0.967840, 0.971889, 0.975938, 0.979988, 0.984038, 0.988089, 0.992140, 0.996191, 1.000242, 1.004294, 1.008347, 1.012399, 1.016452, 1.020506, 1.024560, 1.028614, 1.032668, 1.036723, 1.040778, 1.044834, 1.048890, 1.052946, 1.057003, 1.061060, 1.065117, 1.069175, 1.073233, 1.077291, 1.081350, 1.085409, 1.089468, 1.093528, 1.097588, 1.101649, 1.105710, 1.109771, 1.113833, 1.117895, 1.121957, 1.126020, 1.130083, 1.134146, 1.138209, 1.142273, 1.146338, 1.150403, 1.154468, 1.158533, 1.162599, 1.166665, 1.170731, 1.174798, 1.178865, 1.182932, 1.187000, 1.191068, 1.195137, 1.199206, 1.203275, 1.207344, 1.211414, 1.215484, 1.219555, 1.223625, 1.227697, 1.231768, 1.235840, 1.239912, 1.243984, 1.248057, 1.252130, 1.256204, 1.260278, 1.264352, 1.268426, 1.272501, 1.276576, 1.280651, 1.284727, 1.288803, 1.292880, 1.296956, 1.301033, 1.305111, 1.309189, 1.313267, 1.317345, 1.321424, 1.325503, 1.329582, 1.333661, 1.337741, 1.341822, 1.345902, 1.349983, 1.354064, 1.358146, 1.362228, 1.366310, 1.370392, 1.374475, 1.378558, 1.382642, 1.386725, 1.390809, 1.394894, 1.398978, 1.403063, 1.407149, 1.411234, 1.415320, 1.419406, 1.423493, 1.427579, 1.431667, 1.435754, 1.439842, 1.443930, 1.448018, 1.452107, 1.456196, 1.460285, 1.464374, 1.468464, 1.472554, 1.476645, 1.480735, 1.484826, 1.488918, 1.493009, 1.497101, 1.501193, 1.505286, 1.509379, 1.513472, 1.517565, 1.521659, 1.525753, 1.529847, 1.533942, 1.538036, 1.542131, 1.546227, 1.550323, 1.554418, 1.558515, 1.562611, 1.566708, 1.570805, 1.574903, 1.579000, 1.583098, 1.587197, 1.591295, 1.595394, 1.599493, 1.603592, 1.607692, 1.611792, 1.615892, 1.619993, 1.624093, 1.628194, 1.632296, 1.636397, 1.640499, 1.644601, 1.648704, 1.652806, 1.656909, 1.661012, 1.665116, 1.669220, 1.673324, 1.677428, 1.681532, 1.685637, 1.689742, 1.693848, 1.697953, 1.702059, 1.706165, 1.710272, 1.714378, 1.718485, 1.722593, 1.726700, 1.730808, 1.734916, 1.739024, 1.743132, 1.747241, 1.751350, 1.755459, 1.759569, 1.763679, 1.767789, 1.771899, 1.776009, 1.780120, 1.784231, 1.788343, 1.792454, 1.796566, 1.800678, 1.804790, 1.808903, 1.813015, 1.817128, 1.821242, 1.825355, 1.829469, 1.833583, 1.837697, 1.841812, 1.845926, 1.850041, 1.854157, 1.858272, 1.862388, 1.866504, 1.870620, 1.874736, 1.878853, 1.882970, 1.887087, 1.891204, 1.895322, 1.899439, 1.903557, 1.907676, 1.911794, 1.915913, 1.920032, 1.924151, 1.928270, 1.932390, 1.936510, 1.940630, 1.944750, 1.948871, 1.952992, 1.957112, 1.961234, 1.965355, 1.969477, 1.973599, 1.977721, 1.981843, 1.985966, 1.990088, 1.994211, 1.998334, 2.002458, 2.006581, 2.010705, 2.014829, 2.018953, 2.023078, 2.027203, 2.031327, 2.035453, 2.039578, 2.043703, 2.047829, 2.051955, 2.056081, 2.060207, 2.064334, 2.068461, 2.072588, 2.076715, 2.080842, 2.084970, 2.089097, 2.093225, 2.097353, 2.101482, 2.105610, 2.109739, 2.113868, 2.117997, 2.122127, 2.126256, 2.130386, 2.134516, 2.138646, 2.142776, 2.146907, 2.151037, 2.155168, 2.159299, 2.163430, 2.167562, 2.171693, 2.175825, 2.179957, 2.184089, 2.188222, 2.192354, 2.196487, 2.200620, 2.204753, 2.208886, 2.213020, 2.217153, 2.221287, 2.225421, 2.229555, 2.233690, 2.237824, 2.241959, 2.246094, 2.250229, 2.254364, 2.258499, 2.262635, 2.266770, 2.270906, 2.275042, 2.279179, 2.283315, 2.287452, 2.291588, 2.295725, 2.299862, 2.303999, 2.308137, 2.312274, 2.316412, 2.320550, 2.324688, 2.328826, 2.332964, 2.337103, 2.341241, 2.345380, 2.349519, 2.353658, 2.357798, 2.361937, 2.366076, 2.370216, 2.374356, 2.378496, 2.382636, 2.386777, 2.390917, 2.395058, 2.399198, 2.403339, 2.407480, 2.411622, 2.415763, 2.419904, 2.424046, 2.428188, 2.432330, 2.436472, 2.440614, 2.444756, 2.448899, 2.453041, 2.457184, 2.461327, 2.465470, 2.469613, 2.473756, 2.477899, 2.482043, 2.486187, 2.490330, 2.494474, 2.498618, 2.502763, 2.506907, 2.511051, 2.515196, 2.519340, 2.523485, 2.527630, 2.531775, 2.535920, 2.540066, 2.544211, 2.548357, 2.552502, 2.556648, 2.560794, 2.564940, 2.569086, 2.573232, 2.577378, 2.581525, 2.585671, 2.589818, 2.593965, 2.598112, 2.602259, 2.606406, 2.610553, 2.614700, 2.618848, 2.622995, 2.627143, 2.631291, 2.635439, 2.639586, 2.643734, 2.647883, 2.652031, 2.656179, 2.660328, 2.664476, 2.668625, 2.672774, 2.676922, 2.681071, 2.685220, 2.689369, 2.693519, 2.697668, 2.701817, 2.705967, 2.710116, 2.714266, 2.718416, 2.722565, 2.726715, 2.730865, 2.735015, 2.739166, 2.743316, 2.747466, 2.751617, 2.755767, 2.759918, 2.764068, 2.768219, 2.772370, 2.776521, 2.780672, 2.784823, 2.788974, 2.793125, 2.797276, 2.801427, 2.805579, 2.809730, 2.813882, 2.818033, 2.822185, 2.826337, 2.830489, 2.834640, 2.838792, 2.842944, 2.847096, 2.851249, 2.855401, 2.859553, 2.863705, 2.867858, 2.872010, 2.876163, 2.880315, 2.884468, 2.888620, 2.892773, 2.896926, 2.901079, 2.905231, 2.909384, 2.913537, 2.917690, 2.921843, 2.925996, 2.930150, 2.934303, 2.938456, 2.942609, 2.946763, 2.950916, 2.955070, 2.959223, 2.963376, 2.967530, 2.971684, 2.975837, 2.979991, 2.984145, 2.988298, 2.992452, 2.996606, 3.000760, 3.004914, 3.009068, 3.013222, 3.017376, 3.021530, 3.025684, 3.029838, 3.033992, 3.038146, 3.042300, 3.046454, 3.050608, 3.054763, 3.058917, 3.063071, 3.067225, 3.071380, 3.075534, 3.079688, 3.083843, 3.087997, 3.092152, 3.096306, 3.100460, 3.104615, 3.108769, 3.112924, 3.117078, 3.121233, 3.125387, 3.129542, 3.133696, 3.137851, 3.142005, 3.146160, 3.150315, 3.154469, 3.158624, 3.162778, 3.166933, 3.171088, 3.175242, 3.179397, 3.183551, 3.187706, 3.191860, 3.196015, 3.200170, 3.204324, 3.208479, 3.212633, 3.216788, 3.220942, 3.225097, 3.229252, 3.233406, 3.237561, 3.241715, 3.245870, 3.250024, 3.254179, 3.258333, 3.262487, 3.266642, 3.270796, 3.274951, 3.279105, 3.283259, 3.287414, 3.291568, 3.295722, 3.299877, 3.304031, 3.308185, 3.312339, 3.316494, 3.320648, 3.324802, 3.328956, 3.333110, 3.337264, 3.341418, 3.345572, 3.349726, 3.353880, 3.358034, 3.362188, 3.366342, 3.370496, 3.374649, 3.378803, 3.382957, 3.387110, 3.391264, 3.395418, 3.399571, 3.403725, 3.407878, 3.412032, 3.416185, 3.420338, 3.424492, 3.428645, 3.432798, 3.436951, 3.441104, 3.445257, 3.449410, 3.453563, 3.457716, 3.461869, 3.466022, 3.470175, 3.474327, 3.478480, 3.482633, 3.486785, 3.490938, 3.495090, 3.499242, 3.503395, 3.507547, 3.511699, 3.515851, 3.520003, 3.524155, 3.528307, 3.532459, 3.536611, 3.540763, 3.544915, 3.549066, 3.553218, 3.557369, 3.561521, 3.565672, 3.569823, 3.573975, 3.578126, 3.582277, 3.586428, 3.590579, 3.594730, 3.598880, 3.603031, 3.607182, 3.611332, 3.615483, 3.619633, 3.623783, 3.627934, 3.632084, 3.636234, 3.640384, 3.644534, 3.648684, 3.652833, 3.656983, 3.661133, 3.665282, 3.669432, 3.673581, 3.677730, 3.681879, 3.686028, 3.690177, 3.694326, 3.698475, 3.702624, 3.706772, 3.710921, 3.715069, 3.719217, 3.723366, 3.727514, 3.731662, 3.735810, 3.739957, 3.744105, 3.748253, 3.752400, 3.756548, 3.760695, 3.764842, 3.768989, 3.773136, 3.777283, 3.781430, 3.785577, 3.789723, 3.793870, 3.798016, 3.802163, 3.806309, 3.810455, 3.814601, 3.818747, 3.822892, 3.827038, 3.831183, 3.835329, 3.839474, 3.843619, 3.847764, 3.851909, 3.856054, 3.860199, 3.864343, 3.868488, 3.872632, 3.876776, 3.880920, 3.885064, 3.889208, 3.893352, 3.897495, 3.901639, 3.905782, 3.909925, 3.914068, 3.918211, 3.922354, 3.926497, 3.930640, 3.934782, 3.938924, 3.943067, 3.947209, 3.951350, 3.955492, 3.959634, 3.963775, 3.967917, 3.972058, 3.976199, 3.980340, 3.984481, 3.988622, 3.992762, 3.996903, 4.001043, 4.005183, 4.009323, 4.013463, 4.017603, 4.021743, 4.025882, 4.030021, 4.034160, 4.038299, 4.042438, 4.046577, 4.050716, 4.054854, 4.058992, 4.063131, 4.067268, 4.071406, 4.075544, 4.079682, 4.083819, 4.087956, 4.092093]
        
        closest = 0
        for i in range(len(li_0_100_every_0_1)):
            if abs(li_0_100_every_0_1[i]-v) < abs(li_0_100_every_0_1[closest]-v):
                closest = i
        return closest*0.1
    
    
    def create_cycle_graph(self):
        N_POINTS_IN_ONE_HOUR = 100
        for e in self.CYCLES[self.mode]:
            for i in range(N_POINTS_IN_ONE_HOUR*e[0]):
                send("add 1,1,"+str(e[1]))

        
    
    def HHhmm_left(self):
        hh = UI.put_0_if_necessary(int(self.time_left / 60))
        mm = UI.put_0_if_necessary(self.time_left % 60)
        return hh+"h"+mm+"m left"
    
    # Returns in minutes the total cycle time
    def total_cycle_time(self):
        t = 0
        for e in self.CYCLES[self.mode]:
            t+=e[0]
        return t*60
            
    def measure_temp(self):
        m = 0
        for i in range(self.N_MEASUREMENTS):
            m += abs(self.adc.raw_to_v(self.adc.read(4, 0)))*1000
            time.sleep(1/self.N_MEASUREMENTS)
        return m/self.N_MEASUREMENTS
    
    def update(self):
        print("updating the oven")
        v = self.measure_temp()
        
        self.ui_update(self.get_temp_from_voltage(v))
    
    # Update the UI in the right order
    def ui_update(self, temp):
        set_text(UI.OVEN_TEMP_TEXT, '{:.0f} C°'.format(temp))
        set_text(UI.OVEN_TIME_LEFT_TEXT, self.HHhmm_left())
        send("j0.val="+str(self.progress_bar))
    def __init__(self, mode):
        self.mode = mode
        self.progress_bar = 0
        self.adc = ADS1115(I2C(id=1, scl=Pin(3), sda=Pin(2), freq=400000), gain=5)
        # probablement inutile : channel1 = [0,1,2,3]
        
        self.time_left = self.total_cycle_time()
        send("page page2")
        self.update()
        self.create_cycle_graph()
        
uart1 = UART(1, 9600)  
uart1.init(9600, bits=8, parity=None, stop=1) # init with given parameters
uart1.write('j0.val=10\r')
end_cmd=b'\xFF\xFF\xFF'

def get_brightness():
    resp = get_cmd("h0.val")
    print(resp)
    return int(min(int.from_bytes(resp[:4], 'little')/256, 100))
def get_cmd(cmd):
    uart1.write("get "+cmd)
    uart1.write(end_cmd)
    time.sleep_ms(100)
    return uart1.read()

def send(cmd):
    uart1.write(cmd)
    uart1.write(end_cmd)
    time.sleep_ms(100)

#print('j0.val=90', file=uart1)
"""
while True:
    print(uart1.readline())
    time.sleep(1)
    print("ouais")
"""

print("STARTING...")
oven = None
send("page page3")
time.sleep(1)
send("page page3")
while True:
    time.sleep(0.5)
    u_read = uart1.read()
    if u_read == UI.IB2_16H_24H:
        oven = Oven(UI.IB2_16H_24H)
    if u_read == UI.IB2_16H_16H:
        oven = Oven(UI.IB2_16H_24H)
    if u_read == UI.UNIMOULD:
        oven = Oven(UI.UNIMOULD)
    if u_read != None:
        print(u_read)
        
    if oven != None:
        oven.update()
    
    # add id, channel, value
    #print("Response:", uart1.read())
