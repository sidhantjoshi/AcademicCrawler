import tkinter
import requests, copy
from Crawler import process, returnText

class BrowserUI(tkinter.Frame):
    def __init__(self, master):
        """
        Initializes the GUI object
        """
        super(BrowserUI, self).__init__(master)        
        self.grid()
        self.widgets()
        self.stack = []
        self.forwardstack = []
        self.sitemap = {}
        self.map = {}
        #Set of keywords obtained by 2-means clustering of academic data.
        #Can be improved
        self.keywords=['anal',    'gian',    'usin',    'day',    'proc',    'wire',    'powe',    'micr',    'data',    'mode',    'ieee',    'tent',    'basi',    'hour',    'talk',    'meth',    'evol',    'secu',    'robo',    'sens',    'busi',    'orga',    'conf',    'perf',    'dyna',    'emer',    'base',    'symp',    'nati',    'inte']
    
    def listDirectory(self, sitemap):
        """
        Lists all entries at the root of the sitemap passed as parameter
        sitemap: An instance of the sitemap
        """
        self.lbox.delete(0, tkinter.END)
        for key, value in sorted(sitemap.items()):
            self.lbox.insert(tkinter.END, key)
            
    def clearRelatedListBox(self):
        """
        Clears the RHS List Box
        """
        self.lbox2.delete(0, tkinter.END)
    
    def clearDuplicates(self):
        """
        Removes all duplicate entries and sorts the entries in 
        alphabetical order, in the RHS List Box
        """
        lines = []
        unique = {}
        for i in range(self.lbox2.size()):
            lines.append(self.lbox2.get(i))
            unique[self.lbox2.get(i)] = None
        self.clearRelatedListBox()
        for key, value in sorted(unique.items()):
            self.lbox2.insert(tkinter.END, key)
        
    def populateWithText(self, url):
        """
        Given a URL, the RHS ListBox is populated with text that might be 
        relevant to field of academia from the page.
        Relevance is decided based on a keyword search.
        url: The URL to be searched.
        """                
        try:
            text = returnText(url)
            lines = text.split('\n')
            for line in lines:
                if line.strip() == '':
                    continue
                original = line.strip()
                line = line.lower()
                for word in line.split():                
                    if len(word) >= 4:
                        word = word[:4]
                    if word in self.keywords:
                        self.lbox2.insert(tkinter.END, original)
                        break
        except:
            pass            
                   
    def populateRelevantTextDriver(self, url):
        """
        A driver function which populates the RHS List Box with relevant text 
        based on a keyword search.
        url: The URL to be searched.
        """
        self.clearRelatedListBox()
        self.populateWithText(url)
        self.clearDuplicates()
        
    def pushSearchTermToStack(self, search_val):
        """
        Converts a URL into an array where each element is demarcated by a '/'
        search_val: URL to be converted into an array
        Returns: An array representation of the URL
        """
        parts=None        
        if '://' in search_val:
            index = search_val.find('://') + 3
            parts = search_val[index:].split('/')
            parts[0] = search_val[:index] + parts[0]
        else:
            parts = search_val.split('/')
        
        while parts and parts[0] == '':
            del parts[0]
        
        while parts and parts[-1] == '':
            del parts[-1]
        
        self.stack = parts[:1]   
        
    def back(self):
        """
        To go up one level in the browser
        """
        if self.stack:
            forward_value = self.stack.pop()
            current = self.getCurrentDirectory()
            self.listDirectory(current)
            
            self.forwardstack.append(forward_value)            
            
            #Print Current Location
            if len(self.stack) == 0:
                url = '/'
            else:
                url = self.getCurrentURL()
                self.populateRelevantTextDriver(url)            
            self.label3['text'] = url
            
                    
    def forward(self):
        """
        To go down one level in the browser
        """
        if self.forwardstack:
            self.stack.append(self.forwardstack[-1])
            self.forwardstack.pop()
            current = self.getCurrentDirectory()
            self.listDirectory(current)
            
            url = self.getCurrentURL()            
            self.label3['text'] = url
            self.populateRelevantTextDriver(url)        
    
    def search(self):
        """
        This is a driver function that is called on clicking the search button
        """
        #Obtain the URL to be searched
        print(self.search_var.get())
        search_val = self.search_var.get()
        self.stack = []
        self.forwardstack = []
        
        #Process the URL to be searched       
        process(self.sitemap, search_val)        
        
        #Display the current directory
        self.pushSearchTermToStack(search_val)
        self.listDirectory(self.sitemap[self.stack[0]])
        
        #Load the relevant text
        self.populateRelevantTextDriver(search_val)            
        
        #Print Current Location
        url = self.getCurrentURL()
        self.label3['text'] = url            
    
    def crawl(self, sitemap):        
        """
        Crawls through all the links saved in an instance of the sitemap.
        sitemap: An instance of the sitemap.
        """
        if not sitemap:
            current = self.getCurrentURL()
            print('Currently in',current)
            #Not going through PDFs.
            #PDFs require separate processing
            if not current.endswith('.pdf'):
                self.populateWithText(current)
                
                url = self.getCurrentURL()                     
                process(self.sitemap, url)
                
        for key in sitemap.keys():
            self.stack.append(key)
            self.crawl(sitemap[key])
            self.stack.pop()
        
    def crawlDriver(self):        
        """
        Driver to the crawler function.
        """
        if len(self.stack) == 0:
            print('Please select a website to crawl')
            return
        #Uses a copy of the current instance of the sitemap to avoid going
        #into an infinte loop
        sitemap_copy = copy.deepcopy(self.sitemap)
        self.crawl(sitemap_copy[self.stack[0]])
        
        #Updates the current directory
        current = self.getCurrentDirectory()
        self.listDirectory(current)
        #Clears duplicate entries
        self.clearDuplicates()
        
        
    def getCurrentURL(self):
        """
        To construct a URL based on the current location in the sitemap
        """
        dir = self.stack[0]
        for item in self.stack[1:]:
            dir += '/' + item
        
        #To deal with redirects
        response = requests.get(dir)
        dir = response.url
        return dir
    
    def getCurrentDirectory(self):
        """
        To make the sitemap reflect the current location.
        """
        current_sitemap = self.sitemap
        for item in self.stack:
            current_sitemap = current_sitemap[item]
        return current_sitemap
    
    def onDouble(self, event):
        """
        Double clicking an entry in the LHS ListBox will make you traverse 
        to that entry in the sitemap.
        event: The double click event.
        """
        widget = event.widget
        selection = widget.curselection()
        value = widget.get(selection[0])        
        self.stack.append(value)
        current = self.getCurrentDirectory()
        print(current)
        self.listDirectory(current)
        
        #Print Current Location
        url = self.getCurrentURL()
        self.label3['text'] = url
        self.populateRelevantTextDriver(url)
        
    def onBrowse(self):
        """
        Browsing an entry in the LHS ListBox will add all the links 
        in that page to the sitemap.
        Browsing will also fetch all relevant text from the page.
        Browsing can be done either by navigating to the page to the browsed OR
        by selecting the link to be browsed from the LHS List Box 
        """
        #Get current selection
        selection = self.lbox.curselection()
        if len(selection) == 0:
            if len(self.stack) == 0:
                print('Please select a website to browse.')
                return
            selected = False
            
        else:
            value = self.lbox.get(selection[0])
            selected = True
            #Get URL for selection
            self.stack.append(value)        
                
        url = self.getCurrentURL()
        print(url)
        
        process(self.sitemap, url)        
        if selected:
            self.stack.pop()
        
        #List Directory
        current = self.getCurrentDirectory()
        self.listDirectory(current)
        self.populateRelevantTextDriver(url)
        
    def widgets(self):
        """
        Adds all the widgets to the page.
        """
        tkinter.Label(self, text="Site Map System", background="#CC0001", font= ("Arial", 16)).grid(row=0, column=0, padx=20)
        self.search_var = tkinter.StringVar()
        
        self.b1 = tkinter.Button(self, text='Back', command=self.back)
        self.b1.grid(row=1, column=0, sticky=tkinter.W, padx=20, pady=10)
        
        self.searchbarLabel = tkinter.Label(self, text="Search Bar")
        self.searchbarLabel.grid(row=1, column=0, padx=5)
        
        self.b5 = tkinter.Button(self, text='Forward', command=self.forward)
        self.b5.grid(row=1, column=0, sticky=tkinter.E, padx=20, pady=10)
        
        self.entry = tkinter.Entry(self, textvariable=self.search_var, width=45)
        self.entry.grid(row=2, column=0, sticky=tkinter.W, padx=20, pady=10)
        
        self.b2=tkinter.Button(self, text='Search', command=self.search)
        self.b2.grid(row=2, column=1, sticky=tkinter.N + tkinter.S + tkinter.E + tkinter.W, padx=20, pady=10)
        
        self.b3=tkinter.Button(self, text='Browse', command=self.onBrowse)
        self.b3.grid(row=2, column=2, sticky=tkinter.N + tkinter.S + tkinter.E + tkinter.W, padx=20, pady=10)
        
        self.b4=tkinter.Button(self, text='Crawl', command=self.crawlDriver)
        self.b4.grid(row=2, column=3, sticky=tkinter.N + tkinter.S + tkinter.E + tkinter.W, padx=20, pady=10)
        
        self.label1 = tkinter.Label(self, text="Sitemap View")
        self.label1.grid(row=3, column=0, sticky=tkinter.W, padx=20, pady=10)
        
        self.label2 = tkinter.Label(self, text="Relevant Text from Page")
        self.label2.grid(row=3, column=1, sticky=tkinter.W, padx=20, pady=10)
        
        self.lbox = tkinter.Listbox(self, width=45, height=15)
        self.lbox.grid(row=4, column=0, columnspan=6, sticky=tkinter.W, padx=20, pady=10)
        self.lbox.bind("<Double-Button-1>", self.onDouble)
        
        self.lbox2 = tkinter.Listbox(self, width=100, height=15)
        self.lbox2.grid(row=4, column=1, columnspan=6, sticky=tkinter.W, padx=20, pady=10)
        

        self.label3 = tkinter.Label(self, text='')
        self.label3.grid(row=5, column=0, columnspan=6, sticky=tkinter.W, padx=20, pady=10)
        
r = tkinter.Tk()
r.geometry("1200x800")
r.title("Browser")
s = BrowserUI(r)
s.mainloop()