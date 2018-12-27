# Parser

A suite of Python web-scraping programs. These programs are extensible, follow the functional programming paradigm, and make few assumptions. These programs are also compatible with Python 2.6+ and Python 3.0+, mostly PEP8 compliant, and use Firebase as a online drop-in database (which can be swapped for another one like AWS, Google Cloud Platform, or Azure). 

# Goals

Here are some functionality and stretch goals designed to keep the programs as extensible and versatile as possible.

1. Compatible with Python 2.6+ and Python 3.0+
2. Functional programming paradigm
3. Single Responsibility (https://en.wikipedia.org/wiki/Single_responsibility_principle) 
4. Clear variable / function names as opposed to writing unmaintainable comments.
5. As Pythonic code as possible (readability over performance)
6. Open to future improvements (multiprocessing, different ways to download data, etc.)

# Programs

## soc.py (formerly main.py)


# Tips
1. You can delete an entire firebase project and start from scratch. You can also create new projects to get a new, free 10gb limit.
2. Often, there are multiple ways to download the data for verification. For example, if we want to test if multiprocessing works and doens't change the data, we can download the data from the program as a txt file and download the data from the multiprocessing version. We diff the files and compare the differences to see if they are valid differences (occuring naturally with time) or not. 
3. The interface design for most of these programs has been updated (from the older parsing programs) to use timing decorators, print statements, and progress bars to improve the developer interface. We can use this information to make meaningful improvements quickly. For example, in the schedule of classes scraper, we list the number of classes. If the multiprocessing version has a different number, we know something went wrong. We can also use the timing information to figure out where we should look to improve. For example, scraping ~200 pages of data gives us around 10 minutes of pure network requests and updates. If we used some form of multiprocessing, we could significantly reduce this time. 
