To estimate the population affected by climate emergency declarations, the system generates a 'popcount' for each country with one more declarations. A popcount is an estimate of the population under CED within a country at a given date. Each declaration that alters the overall population count within a country generates a new popcount record. If a declaration is added at a date prior to existing declarations, the series of popcounts from that date onwards must be regenerated. The popcount series can then be easily used to generate charts and statistics for that country.

Popcounts apply to a country as a whole and do not give any information about populations within areas of a country.

The following admin actions will result in the popcount series being regenerated:
* altering the population for a country
* altering the population for any area within a country (even if that area is not itself declared, it may be part of a larger structure which means its change could result in adjusted overall count)
* adding or removing supplementary parents for an area
* deleting an area
* adding an area
* adding a declaration
* deleting a declaration

When any of these actions are undertaken for a country which has one or more declarations, this marks the country as in need of a popcount update. A button labelled "update popcount" will appear in the top right admin menu on the country page and all area pages within that country. If several edit/add/delete actions are planned for a country, it's best to leave the popcount update until all actions have been completed. All data relating specifically to each country/area will be displayed accurately (e.g. the population number entered for each area will display as entered), but the generated estimate of the population under CED will be out of date until the popcount series is updated.

When the system registers that an update is needed, it keeps track of the earliest date to regenerate popcounts from. If a single declaration is added or removed, the popcount series only needs to be regenerated from that date on. If multiple declarations are added or removed, the popcount series needs to be regenerated from the date of the earliest affected declarations. If population numbers are changed or areas are added or removed, the whole series must be regenerated.

When all editing actions are complete, click "update popcount" to regenerate the series of stored popcounts. This carries out the following series of actions:
* an HTTP request is sent to the `trigger_recount` API endpoint, specifying the country code
* the system determines from its configuration whether it's running in AWS or a local dev environment
* if in a local dev environment, it executes the `trigger_population_recount` method directly
* if executing in AWS, a lambda is invoked which will carry out the recount independently of the web service
* On the page where the update button was clicked, the button should now display 'popcount running' and will no longer be clickable. This 'running' message won't update automatically and will remain visible while the page is still loaded, even if the update has completed in the background.
* When any area or country page is next loaded for that country (or if the original page is reloaded), if the update has completed in the background, there will be no 'update popcount' or 'popcount running' message visible. If the process is still running, the 'running' message will still be displayed.
