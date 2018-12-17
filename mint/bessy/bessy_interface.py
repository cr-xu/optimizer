"""
Machine interface file for the LCLS to ocelot optimizer


"""
from __future__ import absolute_import, print_function
import os
import sys
from collections import OrderedDict
import numpy as np
import pandas as pd

from re import sub
from xml.etree import ElementTree
from shutil import copy
from datetime import datetime

from PyQt5.QtWidgets import QWidget

try:
    import Image
except:
    try:
        from Pillow import Image
    except:
        try:
            from PIL import Image
        except:
            print('No Module named Image')

try:
    import epics
    epics.ca.DEFAULT_CONNECTION_TIMEOUT = 0.1
except ImportError:
    # Ignore the error since maybe no one is trying to use it... we will raise on the ctor.
    pass

from mint.opt_objects import MachineInterface
#from mint.lcls.lcls_devices import LCLSQuad, LCLSDevice


class BESSYMachineInterface(MachineInterface):
    name = 'BESSYMachineInterface'

    def __init__(self, args=None):
        super(BESSYMachineInterface, self).__init__(args)
        self._save_at_exit = False
        self._use_num_points = True

        if 'epics' not in sys.modules:
            raise Exception('No module named epics. LCLSMachineInterface will not work. Try simulation mode instead.')

        self.data = dict()
        self.pvs = dict()


    #@staticmethod
    #def get_params_folder():
    #    """
    #    Returns the path to parameters/lcls folder in this tree.
    #
    #    :return: (str)
    #    """
    #    this_dir = os.path.dirname(os.path.realpath(__file__))
    #    return os.path.realpath(os.path.join(this_dir, '..', '..', 'parameters', 'lcls'))

    #def device_factory(self, pv):
    #    if pv.startswith("QUAD:"):
    #        return LCLSQuad(pv)
    #    d = LCLSDevice(eid=pv)
    #    return d

    def get_value(self, device_name):
        """
        Getter function for lcls.

        :param device_name: (str) PV name used in caput
        :return: (object) Data from the PV. Variable data type depending on PV type
        """
        pv = self.pvs.get(device_name, None)
        if pv is None:
            self.pvs[device_name] = epics.PV(device_name)
            return self.pvs[device_name].get()
        else:
            if not pv.connected:
                return None
            else:
                return pv.get()

    def set_value(self, device_name, val):
        """
        Setter function for lcls.

        :param device_name: (str) PV name used in caput
        :param val: (object) Value to write to device. Variable data type depending on PV type
        """
        pv = self.pvs.get(device_name, None)
        if pv is None:
            self.pvs[device_name] = epics.PV(device_name)
            return None
        else:
            if not pv.connected:
                return None
            else:
                return pv.put(val)

    def get_energy(self):
        """
        Returns the energy.

        :return: (float)
        """
        return self.get_value("BEND:DMP1:400:BDES")

    def get_charge(self):
        """
        Returns the charge.

        :return: (float)
        """
        charge = self.get_value('SIOC:SYS0:ML00:CALC252')
        return charge

    def get_charge_current(self):
        """
        Returns the current charge and current tuple.

        :return: (tuple) Charge, Current
        """
        charge = self.get_charge()
        current = self.get_value('BLEN:LI24:886:BIMAX')
        return charge, current

    def get_losses(self):
        losses = [self.get_value(pv) for pv in self.losspvs]
        return losses

    def logbook(self, gui):
        pass

    def screenShot(self, gui, filename, filetype):
        """
        Takes a screenshot of the whole gui window, saves png and ps images to file
        """
        pass

    def get_obj_function_module(self):
        from mint.bessy import bessy_obj_function
        return bessy_obj_function

    def get_preset_settings(self):
        """
        Return the preset settings to be assembled as Push Buttons at the user interface for quick load of settings.

        :return: (dict) Dictionary with Key being the group name and as value an array of dictionaries following the
        format:
            {"display": "Text of the PushButton", "filename": "my_file.json"}
        """
        # presets = {
        #     "QUADS Optimization": [
        #         {"display": "1. Launch QUADS", "filename": "sase1_1.json"},
        #     ]
        # }
        presets = dict()
        return presets

    def get_quick_add_devices(self):
        """
        Return a dictionary with:
        {
        "QUADS1" : ["...", "..."],
        "QUADS2": ["...", "..."]
        }

        That is converted into a combobox which allow users to easily populate the devices list

        :return: dict
        """
        devs = OrderedDict([
            ("IN20 M. Quads", ["QUAD:IN20:361:BCTRL", "QUAD:IN20:371:BCTRL", "QUAD:IN20:425:BCTRL",
                               "QUAD:IN20:441:BCTRL", "QUAD:IN20:511:BCTRL", "QUAD:IN20:525:BCTRL"]),
            ("LI21 M. Quads", ["QUAD:LI21:201:BCTRL", "QUAD:LI21:211:BCTRL", "QUAD:LI21:271:BCTRL",
                               "QUAD:LI21:278:BCTRL"]),
            ("LI26 201-501", ["QUAD:LI26:201:BCTRL", "QUAD:LI26:301:BCTRL", "QUAD:LI26:401:BCTRL",
                              "QUAD:LI26:501:BCTRL"]),
            ("LI26 601-901", ["QUAD:LI26:601:BCTRL", "QUAD:LI26:701:BCTRL", "QUAD:LI26:801:BCTRL",
                              "QUAD:LI26:901:BCTRL"]),
            ("LTU M. Quads", ["QUAD:LTU1:620:BCTRL", "QUAD:LTU1:640:BCTRL", "QUAD:LTU1:660:BCTRL",
                              "QUAD:LTU1:680:BCTRL"]),
            ("Dispersion Quads", ["QUAD:LI21:221:BCTRL", "QUAD:LI21:251:BCTRL", "QUAD:LI24:740:BCTRL",
                                  "QUAD:LI24:860:BCTRL", "QUAD:LTU1:440:BCTRL", "QUAD:LTU1:460:BCTRL"]),
            ("CQ01/SQ01/Sol.", ["SOLN:IN20:121:BCTRL", "QUAD:IN20:121:BCTRL", "QUAD:IN20:122:BCTRL"]),
            ("DMD PVs", ["DMD:IN20:1:DELAY_1", "DMD:IN20:1:DELAY_2", "DMD:IN20:1:WIDTH_2", "SIOC:SYS0:ML03:AO956"])
        ])
        return devs

    def get_plot_attrs(self):
        """
        Returns a list of tuples in which the first element is the attributes to be fetched from Target class
        to present at the Plot 1 and the second element is the label to be used at legend.

        :return: (list) Attributes from the Target class to be used in the plot.
        """
        return [("values", "statistics"), ("objective_means", "mean")]

    def write_data(self, method_name, objective_func, devices=[], maximization=False, max_iter=0):
        """
        Save optimization parameters to the Database

        :param method_name: (str) The used method name.
        :param objective_func: (Target) The Target class object.
        :param devices: (list) The list of devices on this run.
        :param maximization: (bool) Whether or not the data collection was a maximization. Default is False.
        :param max_iter: (int) Maximum number of Iterations. Default is 0.

        :return: status (bool), error_msg (str)
        """
        try:
            import matlog
        except ImportError as ex:
            print(
                "Error importing matlog, reverting to simlog. The error was: ",
                ex)
            import mint.lcls.simlog as matlog

        def byteify(input):
            if isinstance(input, dict):
                return {byteify(key): byteify(value)
                        for key, value in input.iteritems()}
            elif isinstance(input, list):
                return [byteify(element) for element in input]
            elif isinstance(input, unicode):
                return input.encode('utf-8')
            else:
                return input

        def removeUnicodeKeys(input_dict):  # implemented line 91
            return dict([(byteify(e[0]), e[1]) for e in input_dict.items()])

        print(self.name + " - Write Data: ", method_name)
        try:  # if GP is used, the model is saved via saveModel first
            self.data
        except:
            self.data = {}  # dict of all devices deing scanned

        objective_func_pv = objective_func.eid

        self.data[objective_func_pv] = []  # detector data array
        self.data['DetectorAll'] = []  # detector acquisition array
        self.data['DetectorStat'] = []  # detector mean array
        self.data['DetectorStd'] = []  # detector std array
        self.data['timestamps'] = []  # timestamp array
        self.data['charge'] = []
        self.data['current'] = []
        self.data['stat_name'] = []
        # end try/except
        self.data['pv_list'] = [dev.eid for dev in devices]  # device names
        for dev in devices:
            self.data[dev.eid] = []
        for dev in devices:
            vals = len(dev.values)
            self.data[dev.eid].append(dev.values)
        if vals < len(objective_func.values):  # first point is duplicated for some reason so dropping
            objective_func.values = objective_func.values[1:]
            objective_func.objective_means = objective_func.objective_means[1:]
            objective_func.objective_acquisitions = objective_func.objective_acquisitions[1:]
            objective_func.times = objective_func.times[1:]
            objective_func.std_dev = objective_func.std_dev[1:]
            objective_func.charge = objective_func.charge[1:]
            objective_func.current = objective_func.current[1:]
            try:
                objective_func.losses = objective_func.losses[1:]
            except:
                pass
            objective_func.niter -= 1
        self.data[objective_func_pv].append(objective_func.objective_means)  # this is mean for compat
        self.data['DetectorAll'].append(objective_func.objective_acquisitions)
        self.data['DetectorStat'].append(objective_func.values)
        self.data['DetectorStd'].append(objective_func.std_dev)
        self.data['timestamps'].append(objective_func.times)
        self.data['charge'].append(objective_func.charge)
        self.data['current'].append(objective_func.current)
        self.data['stat_name'].append(objective_func.stats.display_name)
        for ipv in range(len(self.losspvs)):
            self.data[self.losspvs[ipv]] = [a[ipv] for a in objective_func.losses]

        self.detValStart = self.data[objective_func_pv][0]
        self.detValStop = self.data[objective_func_pv][-1]

        # replace with matlab friendly strings
        for key in self.data:
            key2 = key.replace(":", "_")
            self.data[key2] = self.data.pop(key)

        # extra into to add into the save file
        self.data["MachineInterface"] = self.name
        try:
            self.data["epicsname"] = epics.name  # returns fakeepics if caput has been disabled
        except:
            pass
        self.data["BEND_DMP1_400_BDES"] = self.get_value("BEND:DMP1:400:BDES")
        self.data["Energy"] = self.get_energy()
        self.data["ScanAlgorithm"] = str(method_name)  # string of the algorithm name
        self.data["ObjFuncPv"] = str(objective_func_pv)  # string identifing obj func pv
        self.data['DetectorMean'] = str(
            objective_func_pv.replace(":", "_"))  # reminder to look at self.data[objective_func_pv]
        # TODO: Ask Joe if this is really needed...
        #self.data["NormAmpCoeff"] = norm_amp_coeff
        self.data["niter"] = objective_func.niter

        # save data
        self.last_filename = matlog.save("OcelotScan", removeUnicodeKeys(self.data), path='default')  # self.save_path)

        print('Saved scan data to ', self.last_filename)

        # clear for next run
        self.data = dict()

        return True, ""
