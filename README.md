# Chat with your data | Data confident

## About

The objective is to give users the posibility to analyse a dataset without writing code or using a dedicated tool for data analytics. Just ask a question or create a task and the program will respond.

And most importat, the data frame is NOT sent to the LLM.


## What can you ask

This is just a list of usual question asked or tasked performed during a Data Science project. Do not limit to this list an come with oyur use cases.

1. What are the column (variable) names (print each one under the other).
2. Clean the column names. Replace spaces and special characters with underscore.
3. Show the first row of the table.
4. Show the first rows of the table.
5. What types are the variables
6. Make a description of the table. <span style="color:yellow">Problem! Does not know how to add include="all" as argument</span>
7. How many missing values each variables has. (Sort them)
8. Which are the numeric variables <span style="color:yellow">Problem! Assumes by looking at variable name, not testing with code</span>
9.  What are the object variables.
10. Create a box plot for each numeric variable <span style="color:yellow"> Problem! Might have to rephrase a bit. Agains assumes which varaibles are numeric.</span>
11. What is the correlation for numeric variables. <span style="color:yellow">Problem! Assumes by looking at variable name, not testing with code</span>
12. Create a corr plot for numeric variables.
13. How many uniques values each object variable has.
14. Count the number of unique values by each variable.
15. Create a box plot for a <numeric_variable> split by <object_variable>. (use any combination).
16. Check if there is a significant difference between the average <numeric_varaible> split by <object_variable>.
17. Any other statistic test. (numeric split by object)
18. Check outliers for numeric variables. (put different limits)
19. Remove the outliers.
20. Standardize the <numeric_variable> and save it with a separate name.
21. Transform <object_variable> into one hot encoding (give details on how to do it)
22. Remove variables.
23. Create a certain ML model. Use <variable> as label. <span style="color:yellow">Problem! The Json respons might not be well formated.</span>
