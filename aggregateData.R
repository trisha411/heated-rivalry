library(tidyverse)

setwd() # set working directory to heated rivalry repository

# HEAT VULNERABILITY INDEX
hvi <- read_csv("data/Heat_Vulnerability_Index_Rankings_20260326.csv")
hvi <- hvi %>% rename(zip = "ZIP Code Tabulation Area (ZCTA) 2020") %>%
  rename(HVI = "Heat Vulnerability Index (HVI)")

# POPULATION DENSITY (2020 CENSUS)
density <- read_csv("data/us_population_density_by_zip_september2020.csv")
density <- density %>% filter(zip %in% hvi$zip) %>% select(c("zip", "population_density"))

# NATURAL GAS USAGE 2010
nat_gas <- read_csv("data/Natural_Gas_Consumption_by_ZIP_Code_-_2010_20260326.csv")
nat_gas <- nat_gas %>% select(c('Zip Code', "Consumption (therms)")) %>% 
  rename(gas2010_therms = "Consumption (therms)")

# STEAM USAGE 2010
steam <- read_csv("data/Steam_Consumption_by_ZIP_Code_-_2010_20260326.csv")
steam <- steam %>% separate(ZIP, into = c("zip", "lat", "lon"), sep = " ") %>% 
  select(c("zip", "Consumption (Mg)")) %>% 
  rename(steam2010_Mg = "Consumption (Mg)")

# DAILY TEMPERATURE (MAY 15 TO SEPTEMBER 15, 2018-2025)
temp <- read_csv("data/nyc_temp.csv")
temp <- temp %>% select(c("DATE", "TMAX")) %>%
  rename(date = DATE, max_temp = TMAX)
temp$date <- as.Date(temp$date, format = "%Y-%m-%d")
temp <- temp %>% filter(date >= as.Date(paste(year(date), 05, 15, sep = "-")),
                        date <= as.Date(paste(year(date), 09, 15, sep = "-"))) %>%
  filter(year(date) >= 2018)

# DRINKING FOUNTAINS
fountains <- read_csv("data/Cool_It!_NYC_2020_-_Drinking_Fountains_20260326.csv")
fountains <- fountains %>% rename(status = "DF Activated", zip = ZIPCode) %>% filter(status == "Activated") %>%
  select(zip)
fountains <- fountains %>% count(zip) %>% filter(zip != 83) %>% rename(fountains = n)


# MAKE DATAFRAME BASE