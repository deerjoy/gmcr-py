# Copyright:   (c) Oskar Petersons 2013

"""Widgets for displaying a conflict's equilibria.

Loaded by the frame_06_equilibria module.
"""

from tkinter import *
from tkinter import ttk
import numpy
from data_01_conflictModel import ConflictModel
from visualizerLauncher import launchVis


class CoalitionSelector(ttk.Frame):
    def __init__(self,master,conflict,solOwner):
        ttk.Frame.__init__(self,master)
        
        self.conflict = conflict
        self.owner = solOwner
        self.coalitionVar = StringVar()
        self.statusVar  = StringVar()
        
        self.label = ttk.Label(self,text="Coalitions:")
        self.label.grid(row=0,column=0,sticky=(N,S,E,W))
        self.entry = ttk.Entry(self,textvariable=self.coalitionVar,validate='key')
        vcmd = self.entry.register(self.onChange)
        self.entry.configure(validatecommand=(vcmd,'%P'))
        self.entry.grid(row=0,column=1,sticky=(N,S,E,W))
        self.statusLabel = ttk.Label(self,textvariable=self.statusVar)
        self.statusLabel.grid(row=0,column=2,sticky=(N,S,E,W))
        
        self.columnconfigure(1,weight=1)
        
        self.refresh()
        
    def refresh(self):
        if self.conflict.coalitions is None:
            self.coalitionVar.set(str([i+1 for i in range(len(self.conflict.decisionMakers))])[1:-1])
        else:
            coalitionsIdx =[]
            for co in self.conflict.coalitions:
                if not co.isCoalition:
                    coalitionsIdx.append(self.conflict.decisionMakers.index(co)+1)
                else:
                    coDMidxs = []
                    for dm in co.members:
                        coDMidxs.append(self.conflict.decisionMakers.index(dm)+1)
                    coalitionsIdx.append(coDMidxs)
            self.coalitionVar.set(str(coalitionsIdx)[1:-1])
        self.statusVar.set("Input OK.")
            
    def onChange(self,newCoalitions):
        try:
            newCoIdxs = eval("["+newCoalitions+"]")
        except:
            self.statusVar.set("Invalid Syntax.")
            return True
        numDMs = len(self.conflict.decisionMakers)
        newCos = []
        seen = []
        areCoalitions = False
        for itm in newCoIdxs:
            if type(itm) is int:
                if itm in seen:
                    self.statusVar.set("%s appears more than once."%itm)
                    return True
                elif (itm > numDMs) or (itm < 1):
                    self.statusVar.set("%s is not a valid DM number."%itm)
                    return True
                else:
                    seen.append(itm)
                    newCos.append(self.conflict.decisionMakers[itm-1])
            elif type(itm) is list:
                newCoMembers = []
                for itm2 in itm:
                    if type(itm2) is not int:
                        self.statusVar.set("%s is an invalid entry"%itm2)
                        return True
                    else:
                        if itm2 in seen:
                            self.statusVar.set("%s appears more than once."%itm2)
                            return True
                        elif (itm2 > numDMs) or (itm2 < 1):
                            self.statusVar.set("%s is not a valid DM number."%itm2)
                            return True
                        else:
                            seen.append(itm2)
                            newCoMembers.append(self.conflict.decisionMakers[itm2-1])
                newCos.append(self.conflict.newCoalition(newCoMembers))
                areCoalitions = True
            else:
                self.statusVar.set("%s is an invalid entry"%itm)
                return True
        if len(seen) == numDMs:
            self.statusVar.set("Input OK.")
            if areCoalitions:
                self.conflict.coalitions = newCos
            else:
                self.conflict.coalitions = None
            self.event_generate("<<CoalitionsChanged>>")
        else:
            self.statusVar.set("Missing DMs"%([x+1 for x in range(numDMs) if x+1 not in seen]))
        return True
        
        
class OptionFormSolutionTable(ttk.Frame):
    def __init__(self,master,conflict,solOwner):
        ttk.Frame.__init__(self,master)
        
        self.conflict = conflict
        self.owner = solOwner
        
        #widgets
        self.tableCanvas = Canvas(self)
        self.table = ttk.Frame(self.tableCanvas)
        self.scrollY = ttk.Scrollbar(self, orient=VERTICAL,command = self.tableCanvas.yview)
        self.scrollX = ttk.Scrollbar(self, orient=HORIZONTAL,command = self.tableCanvas.xview)
        
        #configuration
        self.columnconfigure(0,weight=1)
        self.rowconfigure(0,weight=1)
        
        def resize(event):
            self.tableCanvas.configure(scrollregion=self.tableCanvas.bbox("all"))
        
        self.tableCanvas.grid(column=0,row=0,sticky=(N,S,E,W))
        self.scrollY.grid(column=1,row=0,sticky=(N,S,E,W))
        self.scrollX.grid(column=0,row=1,sticky=(N,S,E,W))
        self.tableCanvas.configure(yscrollcommand=self.scrollY.set)
        self.tableCanvas.configure(xscrollcommand=self.scrollX.set)
        self.tableCanvas.create_window((0,0),window=self.table,anchor='nw')
        self.table.bind("<Configure>",resize)
        
        self.style = ttk.Style()
        #self.style.configure('states.TLabel',background="green")
        self.style.configure('yn.TLabel',background="white")
        #self.style.configure('payoffs.TLabel',background="green")
        self.style.configure('stabilities.TLabel',background="white")
        
        self.refresh()
    
    def refresh(self):
        rowCount = len(self.conflict.options)+len(self.conflict.decisionMakers)+2+6
        
        columnCount = len(self.conflict.feasibles)+2
        tableData = numpy.zeros((rowCount,columnCount),dtype="<U20")
        
        #labels
        tableData[0,1] = "Ordered"
        tableData[1,1] = "Decimal"
        
        ##DMs and options
        currRow = 2
        for i,dm in enumerate(self.conflict.decisionMakers):
            tableData[currRow,0] = "%s - %s"%(i+1,dm.name)
            for opt in dm.options:
                tableData[currRow,1] = opt.name
                currRow += 1
                
        ##payoff labels
        for dm in self.conflict.decisionMakers:
            tableData[currRow,0:2] = ["Payoff For:",dm.name]
            currRow += 1
            
        ##stability type labels
        for st in ['Nash','GMR','SEQ','SIM','SEQ & SIM','SMR']:
            tableData[currRow,1] = st
            currRow += 1
                
        #fill states and stabilities
        currCol = 2
        feasibles = self.conflict.feasibles
        for state in range(len(feasibles)):
            newCol = [feasibles.ordered[state],feasibles.decimal[state]]+list(feasibles.yn[state])
            for dm in self.conflict.decisionMakers:
                newCol.append(dm.payoffs[state])
            newCol += [("Y" if stability else "") for stability in self.owner.sol.allEquilibria[:,state]]
            tableData[:,currCol] = newCol
            currCol += 1
            
            
        
        #push to display
        
        for child in self.table.winfo_children():
            child.destroy()
        
        for row in range(tableData.shape[0]):
            if row<2:
                tag = "states"
            elif row<(len(self.conflict.options)+2):
                tag = "yn"
            elif row<(len(self.conflict.options)+len(self.conflict.decisionMakers)+2):
                tag = "payoffs"
            else:
                tag = "stabilities"
            for col in range(tableData.shape[1]):
                newEntry = ttk.Label(self.table,text=tableData[row,col],style=tag+".TLabel")
                newEntry.grid(row=row,column=col,sticky=(N,S,E,W))
                
                
                
class LogNarrator(ttk.Frame):
    def __init__(self,master,conflict,solOwner):
        ttk.Frame.__init__(self,master)
        
        self.conflict = conflict
        self.owner = solOwner
        
        self.dmVar = StringVar()
        self.stateVar = StringVar()
        self.eqTypeVar = StringVar()
        self.useCoalitions = False
        
        self.dmSel = ttk.Combobox(self,textvariable=self.dmVar,state='readonly')
        self.dmSel.grid(column=0,row=0,sticky=(N,S,E,W),padx=3,pady=3)

        self.stateSel = ttk.Combobox(self,textvariable=self.stateVar,state='readonly')
        self.stateSel.grid(column=1,row=0,sticky=(N,S,E,W),padx=3,pady=3)

        self.eqTypeSel = ttk.Combobox(self,textvariable=self.eqTypeVar,state='readonly')
        self.eqTypeSel['values'] = ('Nash','GMR','SEQ','SIM','SMR')
        self.eqTypeSel.grid(column=2,row=0,columnspan = 2,sticky=(N,S,E,W),padx=3,pady=3)
        
        self.equilibriumNarrator = Text(self, wrap='word')
        self.equilibriumNarrator.grid(column=0,row=1,columnspan=3,sticky=(N,S,E,W))

        self.eqNarrScrl = ttk.Scrollbar(self, orient=VERTICAL,command = self.equilibriumNarrator.yview)
        self.equilibriumNarrator.configure(yscrollcommand=self.eqNarrScrl.set)
        self.eqNarrScrl.grid(column=3,row=1,sticky=(N,S,E,W))
        
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)
        self.columnconfigure(2,weight=1)
        self.rowconfigure(1,weight=1)
        
        self.dmSel.bind('<<ComboboxSelected>>',self.refreshNarration)
        self.stateSel.bind('<<ComboboxSelected>>',self.refreshNarration)
        self.eqTypeSel.bind('<<ComboboxSelected>>',self.refreshNarration)
        
        self.refresh()
        
    def refresh(self):
        if self.conflict.coalitions is None:
            self.useCoalitions = False
            self.dmSel['values'] = tuple([dm.name for dm in self.conflict.decisionMakers])
        else:
            self.useCoalitions = True
            self.dmSel['values'] = tuple([co.name for co in self.conflict.coalitions])
        self.dmSel.current(0)
        self.stateSel['values'] = tuple(self.conflict.feasibles.ordered)
        self.stateSel.current(0)
        self.eqTypeSel.current(0)
        
    def refreshNarration(self,*args):
        self.equilibriumNarrator.delete('1.0','end')
        if self.useCoalitions:
            dm = self.conflict.coalitions[self.dmSel.current()]
        else:
            dm = self.conflict.decisionMakers[self.dmSel.current()]
        state = self.stateSel.current()
        eqType = self.eqTypeVar.get()
        if eqType == "Nash":
            newText = self.owner.sol.nash(dm,state)[1]
        elif eqType == 'GMR':
            newText = self.owner.sol.gmr(dm,state)[1]
        elif eqType == 'SEQ':
            newText = self.owner.sol.seq(dm,state)[1]
        elif eqType == 'SIM':
            newText = self.owner.sol.sim(dm,state)[1]
        elif eqType == 'SMR':
            newText = self.owner.sol.smr(dm,state)[1]
        else:
            newText = "Error: bad equilibrium type selected."
        self.equilibriumNarrator.insert('1.0',newText)
        
        
class Exporter(ttk.Frame):
    def __init__(self,master,conflict,solOwner):
        ttk.Frame.__init__(self,master)
        
        self.conflict = conflict
        self.owner = solOwner

        self.RMdumpBtnJSON = ttk.Button(self,text='Save Reachability as JSON',command=self.saveToJSON)
        self.RMdumpBtnJSON.grid(column=0,row=0,sticky=(N,S,E,W),padx=3,pady=3)
        self.visLaunchBtn = ttk.Button(self,text='Launch Visualizer',command=self.loadVis)
        self.visLaunchBtn.grid(row=0,column=1,sticky=(N,S,E,W),padx=3,pady=3)
        
    def saveToJSON(self,event=None):
        fileName = filedialog.asksaveasfilename(defaultextension= '.json',
                                        filetypes = (("JSON files", "*.json")
                                                     ,("All files", "*.*") ),
                                        parent=self)
        if fileName:
            self.owner.sol.saveJSON(fileName)
                                        
    def loadVis(self,event=None):
        self.owner.sol.saveJSON("gmcr-vis/json/conflictData.json")
        launchVis()





def main():
    root = Tk()
    root.columnconfigure(0,weight=1)
    root.rowconfigure(0,weight=1)

    g1 = ConflictModel('Prisoners.gmcr')


    res = LogResultDisp(root,g1)
    res.grid(column=0,row=0,sticky=(N,S,E,W))


    root.mainloop()

if __name__ == '__main__':
    main()
