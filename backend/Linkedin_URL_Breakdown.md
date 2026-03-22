# URL Breakdown:

1. `currentJobId=4184090151`
    - Specifies a job currently being viewed. Changing or removing this does not affect the search results.
2. `distance=25`
    - Controls the job search radius in miles.
    - Example: If you want to search within 50 miles, change it to `distance=50`.
3. `f_TPR=r3600`
    - Filters job postings by recency.
    - `r3600` means jobs posted within the last hour.
    - Common values:
        - `r86400` (Last 24 hours)
        - `r604800` (Last week)
        - `r2592000` (Last month)
4. `geoId=103644278`
    - Specifies the geographic location.
    - Example: If searching for jobs in Florida, you need the geoId for Florida.
5. `keywords=senior%20operations%20manager`
    - Determines the job title or keywords being searched.
    - `%20` represents spaces, so this query searches for “Senior Operations Manager.”
    - To search for “Director of Operations,” change it to `keywords=Director%20of%20Operations`.
6. `location=United%20States`
    - Defines the search location.
    - Example: Searching in Florida? Change it to `location=Florida`.
7. `origin=JOB_SEARCH_PAGE_JOB_FILTER`
    - Indicates that the search is being filtered from the job search page. You can ignore this.
8. `sortBy=R`
    - Sorts results by relevance (`R`).
    - Options:
        - `DD` (Date posted)
        - `R` (Relevance)

9. `f_JT: JOB TYPE` -> Value=Meaning => F=Full-time|P=Part-time|C=Contract|T=Temporary|I=Internship|V=Volunteer|O=Other
10. `f_EL`: EXPERIENCE LEVEL ->Value=Meaning => 1=Internship|2=Entry level (SWE1)|3=Associate|4=Mid-Senior|5=Director|6=Executive
11. `f_wt`: Job type filter. Common values:
                    ONSITE = "1"
                    REMOTE = "2"
                    HYBRID = "3"