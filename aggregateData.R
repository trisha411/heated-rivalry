library(tidyverse)

setwd() # set working directory to heated rivalry repository

# HEAT VULNERABILITY INDEX
hvi <- read_csv("data/Heat_Vulnerability_Index_Rankings_20260326.csv")
hvi <- hvi %>% rename(zip = "ZIP Code Tabulation Area (ZCTA) 2020") %>%
  rename(HVI = "Heat Vulnerability Index (HVI)") %>%
  mutate(zip = as.character(zip)) 

# POPULATION DENSITY (2020 CENSUS)
# note: this doesn't have all zip codes..
density <- read_csv("data/us_population_density_by_zip_september2020.csv")
density <- density %>% select(c("zip", "population_density", "population")) %>%
  mutate(zip = as.character(zip))

# NATURAL GAS USAGE 2010
nat_gas <- read_csv("data/Natural_Gas_Consumption_by_ZIP_Code_-_2010_20260326.csv")
nat_gas <- nat_gas %>% select(c('Zip Code', "Consumption (therms)")) %>% 
  rename(gas2010_therms = "Consumption (therms)", zip = "Zip Code") %>% 
  separate(zip, into = c("zip", "lat", "lon"), sep = " ") %>% select(zip, gas2010_therms)
  mutate(zip = as.character(zip))
nat_gas <- nat_gas %>% group_by(zip) %>% summarize(gas_therms = sum(gas2010_therms, na.rm = TRUE))

# STEAM USAGE 2010
steam <- read_csv("data/Steam_Consumption_by_ZIP_Code_-_2010_20260326.csv")
steam <- steam %>% separate(ZIP, into = c("zip", "lat", "lon"), sep = " ") %>% 
  select(c("zip", "Consumption (Mg)")) %>% 
  rename(steam2010_Mg = "Consumption (Mg)") %>%
  mutate(zip = as.character(zip))
steam <- steam %>% group_by(zip) %>% summarize(steam_Mg = sum(steam2010_Mg, na.rm = TRUE))

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
fountains <- fountains %>% count(zip) %>% filter(zip != 83) %>% rename(fountains = n) %>%
  mutate(zip = as.character(zip))

# 311 CALLS
calls <- read_csv("data/ML_311_FINAL.csv")
calls$date <- as.Date(calls$date, format = "%m/%d/%y")
calls <- calls %>% rename(zip = zip_code) %>% 
  filter(date >= as.Date(paste(year(date), 05, 15, sep = "-")),
         date <= as.Date(paste(year(date), 09, 15, sep = "-"))) %>% unique() %>%
  mutate(zip = as.character(zip))
  
# STREET TREE COUNT (2015 census)
trees <- read_csv("data/ML_treecountperzip.csv")
trees <- trees %>% filter(zipcode != 83) %>% rename(zip = zipcode) %>%
  mutate(zip = as.character(zip))


# MERGE TIME CONSTANT DATA
time_const <- full_join(hvi, fountains, by = "zip")
time_const <- full_join(time_const, nat_gas, by = "zip")
time_const <- full_join(time_const, steam, by = "zip")
time_const <- full_join(time_const, trees, by = "zip")
density <- density %>% filter(zip %in% time_const$zip)
time_const <- full_join(time_const, density, by = "zip")


# MERGE WITH 311 CALLS
final_data <- full_join(calls, time_const, by = "zip")
final_data <- full_join(final_data, temp, by = c("date"))


# export
write.csv(final_data, file = "data/allData.csv")
