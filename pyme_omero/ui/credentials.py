
import wx
import logging

logger = logging.getLogger(__name__)

class CredentialConfigFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "OMERO Credentials",size=(350,175))
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.user_label = wx.StaticText(self, label="username", pos=(20,20))
        h_sizer.Add(self.user_label, wx.EXPAND | wx.ALL, 10)
        self.user = wx.TextCtrl(self, value="", size=(500,-1))
        h_sizer.Add(self.user, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.password_label = wx.StaticText(self, label="password", pos=(20,60))
        h_sizer.Add(self.password_label, wx.EXPAND | wx.ALL, 10)
        self.password = wx.TextCtrl(self, value="", size=(500,-1))
        h_sizer.Add(self.password, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.address_label = wx.StaticText(self, label="server address", pos=(20,100))
        h_sizer.Add(self.address_label, wx.EXPAND | wx.ALL, 10)
        self.address = wx.TextCtrl(self, value="", size=(500,-1))
        h_sizer.Add(self.address, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.port_label = wx.StaticText(self, label="server port", pos=(20,100))
        h_sizer.Add(self.port_label, wx.EXPAND | wx.ALL, 10)
        self.port = wx.TextCtrl(self, value=str(4064), size=(500,-1))
        h_sizer.Add(self.port, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.save_button =wx.Button(self, label="Save", pos=(110,160))
        self.save_button.Bind(wx.EVT_BUTTON, self.OnSave)
        h_sizer.Add(self.save_button, wx.EXPAND | wx.ALL, 10)
        self.close_button =wx.Button(self, label="Cancel", pos=(210,160))
        self.close_button.Bind(wx.EVT_BUTTON, self.OnQuit)
        h_sizer.Add(self.close_button, wx.EXPAND | wx.ALL, 10)
        v_sizer.Add(h_sizer)
        
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.SetSizer(v_sizer)

    def OnSave(self, wx_event):
        from PYME import config
        import yaml
        import os

        cred = {
            'user': self.user.GetValue(),
            'password': self.password.GetValue(),
            'address': self.address.GetValue(),
            'port': int(self.port.GetValue())
        }

        if any([str(v) == '' for v in cred.values()]):
            logger.error('Cannot properly configure with any entries left blank')
            return

        plugin_config_dir = os.path.join(config.user_config_dir, 'plugins', 'config')
        os.makedirs(plugin_config_dir, exist_ok=True)
        with open(os.path.join(plugin_config_dir, 'pyme-omero'), 'w') as f:
            yaml.dump(cred, f)
        
        self.OnQuit(wx_event)

    def OnQuit(self, wx_event):
        self.result_name = None
        self.Destroy()
