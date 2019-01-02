Parser
======

A suite of Python web-scraping programs. These programs are extensible, follow the functional programming paradigm, and make few assumptions. These programs are also compatible with Python 2.6+ and Python 3.0+, mostly PEP8 compliant, and use Firebase as a online drop-in database (which can be swapped for another one like AWS, Google Cloud Platform, or Azure). 

Goals
-----

Here are some functionality and stretch goals designed to keep the programs as extensible and versatile as possible.

1. Compatible with Python 2.6+ and Python 3.0+
2. Functional programming paradigm
3. `Single Responsibility <https://en.wikipedia.org/wiki/Single_responsibility_principle/>`_ 
4. Clear variable / function names as opposed to writing unmaintainable comments.
5. As Pythonic code as possible (readability over performance)
6. Open to future improvements (multiprocessing, different ways to download data, etc.)
7. Measure how often students visit certain sites and see if we can include that data into the current programs. For example, students visit Rate My Professor a lot. We can't include that data due to copyright restrictions. However, if students visit the restriction codes website to tell what a code means, we can integrate that data to make the user take one less visit to one less site. 

Programs
-----

catalog.py
~~~~~~~~~~~~
**Description**: This program fetches the course descriptions, prerequisites, restrictions, and correct (unabbreviated) titles for each course in the entire catalog (we even fetch course data that isn't in the schedule of classes). This program need only run every once in a while, because the data rarely changes except for the addition of a new department or course. 

*Dependencies*: None. We usually run this first, ensure the data is in Firebase, and then proceed with the rest.

*Features*: Described above.

soc.py
~~~~~~~~~~~~
*Description*: This program is responsible for fetching the latest course data from the `Schedule of Classes <https://act.ucsd.edu/scheduleOfClasses/scheduleOfClassesStudent.htm/>`_ for a given or the latest quarter, and uploading that data to Firebase after parsing, filtering, and comptuing some meta data (like seat tracking, waitlist, dei, etc.). 

*Dependencies*: requires catalog.py information in database to update the descriptions, prerequisites, and restrictions of each course. *An important note*: we can't scrape this information from the schedule of classes itself. If we take a look, clicking on the course title, like *Advanced Data Structures* (from CSE 100) redirects us to the `Catalog <https://ucsd.edu/catalog/front/courses.html/>`_ description. 

*Features*: 

1. Seat tracking - Seat information for a course (Ex. CSE 100), based upon the number of seats remaining and available. Will be used to chart the seat-fill rate over time. This has some interesting possiblities, like examining the number of people that enroll during their `enrollment time <https://blink.ucsd.edu/instructors/courses/enrollment/start.html/>`_ to figure out the proposed demographic of a course (50% seniors, 20% juniors, etc. as an example). 
2. Waitlist & DEI - Used to determine if a class is waitlisted or not, and if a class is DEI-approved or not.
3. Write to file, Write to DB - Multiple ways to export the data. Writing to file is helpful for when we want to compare if the data we parsed is accurate (comparing a multiprocessing version to a regular one for example). 
4. Natural Restrictions - Restrictions are formatted. So, instead of having codes like XF JR SR, we have something more like: Open to juniors and seniors only. This more natural language is easier to understand and prevents visiting another site for a restrictions code legend.

cape.py
~~~~~~~~~~~~
*Description*: This program is responsible for fetching the latest CAPE data for all courses for a given quarter. We retrieve that data, update each course object, compute some meta data, and upload the new object to Firebase.

*Dependencies*: we need soc.py to run first. This should be obvious - we need the courses (and their teachers) we are fetching data for. 

*Features*:

1. Aggregate scores for Expected Grade, Received Grade, Study, and % Recommend Teacher. These are compute on a per course per teacher level to allow for a future feature to compare teacher's metrics for a course directly within the website. This will provide at a glance information on which course to consider over another, and which teacher within those courses to consider over another. Probably will be used in a table format or bar chart. 
2. Entire Grade Distributions (breakdown of As, Bs, Cs, P, NP, etc.) per (teacher / course / department). We will use this in two ways. First, we will show this data as a pie chart or bar graph to compare between teachers for a course. Second, we will use the grade distributions per teacher, compared to the ones for the course in general to show the variance this teacher has over the course in general (if they follow the distribution of break from it). Finally, we can also extend this idea to include department averages so we can compare courses' distributions to see which ones we should choose.

More Programs (TODO)
~~~~~~~~~~~~
1. library.py (fetch book store data for a course, if the books are required or not, and maybe some book icons).
2. podcast.py (fetch podcast data for a course).
3. maps.py (fetch map locations with distances between classes) - This is purely optional and doesn't seem like it would provide a lot of benefit. It has a few uses thought, minimize distance between classes as a sorting functionality, show embedded maps of classes inline with course info, and possibly more. 

Tips
-----

1. You can delete an entire firebase project and start from scratch. You can also create new projects to get a new, free 10gb limit.
2. Often, there are multiple ways to download the data for verification. For example, if we want to test if multiprocessing works and doens't change the data, we can download the data from the program as a txt file and download the data from the multiprocessing version. We diff the files and compare the differences to see if they are valid differences (occuring naturally with time) or not. 
3. The interface design for most of these programs has been updated (from the older parsing programs) to use timing decorators, print statements, and progress bars to improve the developer interface. We can use this information to make meaningful improvements quickly. For example, in the schedule of classes scraper, we list the number of classes. If the multiprocessing version has a different number, we know something went wrong. We can also use the timing information to figure out where we should look to improve. For example, scraping ~200 pages of data gives us around 10 minutes of pure network requests and updates. If we used some form of multiprocessing, we could significantly reduce this time. 
