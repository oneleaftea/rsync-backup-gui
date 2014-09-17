from gi.repository import Gtk, Vte, GLib, GObject
from configparser import SafeConfigParser
import os
import subprocess
import threading
import time
import re
from datetime import datetime
    
class MainWindow(Gtk.Window):
    """Main Window of Program"""
    def __init__(self, path):
        super(MainWindow,self).__init__(title="frakkup")
        self.path = path
        self.set_border_width(10)
        self.jobspath = path+'/jobs/'
        self.logspath = path+'/logs/'
        self.connect("destroy", lambda _: Gtk.main_quit())
        
        # Note on Grids: grid.attach(child, left, top, width, height)
        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        self.add(grid)
        
        # Backup list label
        backuplistlabel = Gtk.Label("Saved Backups")
        grid.attach(backuplistlabel, 0, 0, 2, 1)
        
        # Create scrolledwindow which holds Treeview which holds listbox
        self.liststore = Gtk.ListStore(str)
        self.populatelist() # Populate list from list of saved backups
        treeview = Gtk.TreeView(model=self.liststore) 
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.add(treeview)
        scrolledwindow.set_policy(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                  vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        grid.attach_next_to(scrolledwindow, backuplistlabel, Gtk.PositionType.BOTTOM, 2, 5)
        scrolledwindow.set_vexpand(True) # Allow vertical expansion
        treeviewcolumn = Gtk.TreeViewColumn("Backup List")
        treeview.set_headers_visible(headers_visible=False)
        treeview.append_column(treeviewcolumn)
        cellrenderertext = Gtk.CellRendererText()
        treeviewcolumn.pack_start(cellrenderertext, True)
        treeviewcolumn.add_attribute(cellrenderertext, "text", 0)
        
        # Treeselection methods are retrieved from treeview.get_selection()
        self.treeviewselect = treeview.get_selection()
        self.treeviewselect.set_mode(Gtk.SelectionMode.SINGLE)
        self.treeviewselect.connect("changed", self.on_tree_selection_changed)


        # Source/Destination/Saved Backup entries
        sourcelabel = Gtk.Label("Source")
        grid.attach(sourcelabel, 2, 2, 1, 1)
        destinationlabel = Gtk.Label("Destination")
        grid.attach_next_to(destinationlabel, sourcelabel, Gtk.PositionType.BOTTOM, 1, 1)
        separator = Gtk.SeparatorToolItem() 
        grid.attach_next_to(separator, destinationlabel, Gtk.PositionType.BOTTOM, 5, 1)
        savelabel = Gtk.Label("Backup Job")
        grid.attach_next_to(savelabel, separator, Gtk.PositionType.BOTTOM, 1, 1)
        
        self.sourcefield = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.destinationfield = Gtk.FileChooserButton(action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.sourcefield.set_hexpand(True) # allow horizontal expansion
        self.destinationfield.set_hexpand(True)
        self.savefield = Gtk.Entry()
        grid.attach_next_to(self.sourcefield,sourcelabel,Gtk.PositionType.RIGHT,4,1)
        grid.attach_next_to(self.destinationfield,destinationlabel,Gtk.PositionType.RIGHT,4,1)
        grid.attach_next_to(self.savefield,savelabel,Gtk.PositionType.RIGHT,2,1)
        
        # Separator
        separator2 = Gtk.SeparatorToolItem()
        grid.attach_next_to(separator2, scrolledwindow, Gtk.PositionType.BOTTOM, 6, 1)

        # Sudo option
        self.sudocheckbox = Gtk.CheckButton(label="Run as sudo")
        grid.attach_next_to(self.sudocheckbox, separator2, Gtk.PositionType.BOTTOM, 2, 1)
        
        # Additional Rsync Options Fields
        optionslabel = Gtk.Label("Rsync Options: ")
        grid.attach_next_to(optionslabel, self.sudocheckbox, Gtk.PositionType.RIGHT, 1, 1)
        self.optionsfield = Gtk.Entry()
        grid.attach_next_to(self.optionsfield,optionslabel,Gtk.PositionType.RIGHT,5,1)
        self.optionsfield.set_hexpand(True)
        
        # Action Buttons: Top row buttons Definitions, placement, and assignments
        topbuttonbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(topbuttonbox,3,0,4,1)
        self.newbutton = Gtk.Button(label="New")
        self.runbutton = Gtk.Button(label="Run")
        topbuttonbox.add(self.newbutton)
        topbuttonbox.add(self.runbutton)
        self.newbutton.connect("clicked", self.new)
        self.runbutton.connect("clicked", self.runbackup)
        
        # Action Buttons: Side buttons definitions and placement, and assignments
        sidebuttonbox = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach_next_to(sidebuttonbox,self.savefield,Gtk.PositionType.RIGHT,2,1)
        self.savebutton = Gtk.Button(label="Save")
        self.deletebutton = Gtk.Button(label="Delete")
        sidebuttonbox.add(self.savebutton)
        sidebuttonbox.add(self.deletebutton)
        self.savebutton.connect("clicked", self.save)
        self.deletebutton.connect("clicked", self.deletebackup)
                
        self.selected = {} # Dictionary to store source, dest, and name from cfg
        self.readybackup = {} # Dictionary to store source, dest, and name from fields
        
        # Set initial button sensitivity
        self.deletebutton.set_sensitive(False)
        self.savebutton.set_sensitive(False)
        self.runbutton.set_sensitive(False)

        self.mode = 'normal' # Allows signal triggering to occur as normal
        self.show_all()
        
        # Start button sensitivity polling thread
        thread = threading.Thread(target=self.threadpoll)
        thread.daemon = True
        thread.start()
    
    def populatelist(self):
        """Populates the liststore with names of saved backup jobs"""
        for file in sorted(os.listdir(self.jobspath)):
            if file.endswith(".ini"):
                self.liststore.append([file[:-4]])
                
    def on_tree_selection_changed(self,selection):
        """Updates source, destination and name fields"""
        if self.mode != 'saving': # Eliminates side effects when repopulating list
            model, treeiter = selection.get_selected()
            if treeiter != None: # Runs block only when something is selected
                self.selected['name'] = model[treeiter][0]
                #~ print("You selected", self.selected['name']) # Comment out or delete
                self.readconfig()
                self.sourcefield.set_filename(self.selected['source'])
                self.destinationfield.set_filename(self.selected['dest'])
                self.savefield.set_text(self.selected['name'])
                self.sudocheckbox.set_active(self.selected['sudo'] == "True") #Converts to Boolean
                if self.selected['options'] is None:
                    self.optionsfield.set_text('')
                else:
                    self.optionsfield.set_text(self.selected['options'])
    
    def readconfig(self):
        """Reads settings from cfg files"""
        config = SafeConfigParser(allow_no_value=True)
        config.read(self.jobspath+self.selected['name']+'.ini')
        self.selected['source'] = config.get('directories','source')
        self.selected['dest'] = config.get('directories','destination')
        self.selected['options'] = config.get('options', 'options')
        self.selected['sudo'] = config.get('options', 'sudo')

    def new(self,newbutton):
        """Unselects and deletes all fields"""
        self.treeviewselect.unselect_all()
        self.sourcefield.unselect_all()
        self.destinationfield.unselect_all()
        self.savefield.delete_text(0, -1)
        self.sudocheckbox.set_active(False)

    def getreadybackup(self):
        """Stores all fields to a dictionary"""
        self.readybackup["source"] = self.sourcefield.get_filename()+'/'
        self.readybackup["dest"] = self.destinationfield.get_filename()+'/'
        self.readybackup["name"] = self.savefield.get_text()
        self.readybackup["options"] = self.optionsfield.get_text()
        self.readybackup["sudo"] = self.sudocheckbox.get_active()
    
    def runbackup(self,runbutton):
        """Prepares for and launches Rsync in a new window"""
        self.getreadybackup() # Reestablish in case changed between polling loops
        dialog = RunningWindow(self)
        response = dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.CANCEL]:
            pass
            #~ print("backup done") # comment out
        dialog.destroy()

    def save(self,savebutton):
        """Saves fields to a new backup cfg file and repopulates liststore"""
        self.mode = 'saving'
        self.getreadybackup() # Reestablish in case changed between polling loops
        cfgfile = open(self.jobspath+self.readybackup['name']+".ini",'w')
        parser = SafeConfigParser()
        parser.add_section('directories')
        parser.add_section('options')
        parser.set('directories','source',self.readybackup['source'])
        parser.set('directories','destination',self.readybackup['dest'])
        parser.set('options','options',self.readybackup['options'])
        parser.set('options','sudo',str(self.readybackup['sudo']))
        parser.write(cfgfile)
        cfgfile.close()
        self.liststore.clear()
        self.populatelist()
        self.mode = 'normal'
    
    def deletebackup(self,deletebutton):
        """Deletes existing cfg file and repopulates liststore"""
        self.mode = 'saving'
        self.getreadybackup() # Reestablish in case changed between polling loops
        self.filetodelete=self.jobspath+self.readybackup['name']+".ini"
        if (os.path.isfile(self.filetodelete)):
            os.remove(self.filetodelete)
            self.liststore.clear()
            self.populatelist()
            self.new(self.newbutton)
        else:
            print("file doesn't exist")
        self.mode = 'normal'
    
    def threadpoll(self): # Method to get around non thread safety of GTK+
        """Schedules thread with Main thread"""
        while True:
            GLib.idle_add(self.poll)
            time.sleep(0.5)
    
    def poll(self): # Exits gracefully since thread is managed by Main thread.
        """Sets button sensitivity based on field population"""
        if (    self.sourcefield.get_filename() is not None and 
                self.destinationfield.get_filename() is not None):
            self.getreadybackup()
            if len(self.savefield.get_text()) > 0:
                self.savebutton.set_sensitive(True)
                self.filetodelete=self.jobspath+self.readybackup['name']+".ini"
                if (os.path.isfile(self.filetodelete)):
                    self.deletebutton.set_sensitive(True)
                else:
                    self.deletebutton.set_sensitive(False)
            else:
                self.savebutton.set_sensitive(False)
            self.runbutton.set_sensitive(True)
        else:
            self.deletebutton.set_sensitive(False)
            self.savebutton.set_sensitive(False)
            self.runbutton.set_sensitive(False)


class RunningWindow(Gtk.Dialog):
    """Separate window which launches when backup is run"""
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Backup Job", parent, 0)
        self.set_default_size(300, 350)
        now = datetime.now().strftime('%Y%m%d_%H%M%S') # Prepares timestamp
                
        # Define scrolled window and child terminal widget
        self.terminal = Vte.Terminal()
        scrolledterm = Gtk.ScrolledWindow()
        scrolledterm.set_min_content_height(300)
        scrolledterm.set_min_content_width(500)
        scrolledterm.add(self.terminal)
        scrolledterm.set_policy(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                vscrollbar_policy=Gtk.PolicyType.AUTOMATIC)
        self.terminal.fork_command_full( Vte.PtyFlags.DEFAULT, os.environ['HOME'],
                ["/bin/sh"], [], GLib.SpawnFlags.DO_NOT_REAP_CHILD, None, None)
        self.terminal.connect("child-exited", lambda x: self.backupdone(parent.readybackup))        
        
        # Populate box (this dialog window)     
        box = self.get_content_area()
        box.add(scrolledterm)
        self.okbutton = self.add_button("_Ok", Gtk.ResponseType.OK)
        self.cancelbutton = self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        self.cancelbutton.set_sensitive(True)
        self.okbutton.set_sensitive(False) # Hide until job is complete
        self.confirmlabel = Gtk.Label("The backup job is complete. Hit OK to return.")
        box.add(self.confirmlabel)  
        
        self.show_all()
        self.confirmlabel.hide() # Hide until job is complete
        
        # RUN Backup Job: this uses a softlink to be used as a hardlinked location path. 
        # Term "hardlink" used below but may refer to a softlink
        self.hardlink = parent.readybackup["dest"]+"LatestBackup"
        self.newbackuppath = parent.readybackup["dest"]+now
        if os.path.exists(self.hardlink): # Check if softlink exists and is valid
            hardlinkarg = '--link-dest="'+self.hardlink+'"'
        else: # Softlink doesn't exist or is invalid
            a = re.compile("^\d{8}_\d{6}$") # Pattern to match
            matchlist = []
            for prevbackup in sorted(os.listdir(parent.readybackup["dest"])):
                if a.match(prevbackup):
                    matchlist.append(prevbackup)
            if matchlist: # At least one prev backup exists
                newlink = parent.readybackup["dest"]+matchlist[-1]
                hardlinkarg = '--link-dest="'+newlink+'"'
            else: # No previous backup exists
                hardlinkarg = '' # Initializes first backup without hardlinking 
        if parent.readybackup["sudo"]:
            sudoarg = "sudo "
        else:
            sudoarg = ""
        args = [sudoarg+"rsync", "-avWhx", "--progress", "--stats", parent.readybackup["options"], hardlinkarg,
                '--log-file="'+parent.logspath+parent.readybackup["name"]+'backup.txt"',
                '"'+parent.readybackup["source"]+'"', '"'+self.newbackuppath+'"']
        #~ print(' '.join(args)) #Comment out
        command = ' '.join(args)+'; exit\n' # Added 'exit' to trigger exit signal
        length = len(command) # Null terminates command
        self.terminal.feed_child(command, length) # Inputs command into terminal

    
    def backupdone(self,readybackup): # Triggered by child-exited signal
        """
        Shows OK button and label and desensitizes Cancel button
        Creates/Updates Softlinks to point to newest created backup path
        """
        # This only runs after successful backup, called upon "child-exit" signal.
        # Consider adding condition that "Cancel response type" was not detected.
        # Testing indicates this is not necessary since cancelling does not trigger "child-exit"
        # of terminal. Consider putting it in if necessary later on.
        subprocess.call(['ln','-s',self.newbackuppath,readybackup["dest"]+"TempLatestBackup"])
        subprocess.call(['mv','-Tf',readybackup["dest"]+"TempLatestBackup",self.hardlink])
        
        self.okbutton.set_sensitive(True)
        self.cancelbutton.set_sensitive(False)
        self.confirmlabel.show()
        self.set_focus(self.okbutton)


path = os.environ['HOME']+'/.config/frakkup'
if not os.path.exists(path+'/jobs'):
    os.makedirs(path+'/jobs')

if not os.path.exists(path+'/logs'):
    os.makedirs(path+'/logs')
    
if __name__ == "__main__":
    GObject.threads_init() # Optional with latest PyGOBject
    MainWindow(path)
    Gtk.main()

