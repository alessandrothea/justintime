from .. import page_class

def return_obj():
    text="Just-in-Time is a prompt feedback tool designed for ProtoDune. It assesses recorded data coming from detector and trigger, with plots that extract complicated information to examine data quality and fragility. Particularly, trigger record displays are provided that allow users to choose run files and trigger records to analyze and compare. A variety of plots is included, which can be found on the navigation bar. "
    page = page_class.page("Home Page and TR Info", "/",text)
    page.add_plot("01_home_plot")
    
    return(page)