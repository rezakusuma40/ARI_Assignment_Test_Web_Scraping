from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import pandas as pd

# Initialize the WebDriver
Driver='/path/to/my/chromedriver.exe'
driver=webdriver.Chrome(Driver)
driver.implicitly_wait(20)
driver.maximize_window() # there is a bug when using default window size
driver.get('https://www.visionplus.id/movies') # open the main page
# this page lists movies by category
# if a category has more than 20 movies, it has a see more button to see all it's movies

# this loop below scrape movie page url, movie poster url, and category name
category_boxes=driver.find_elements(By.CLASS_NAME, 'swiper-box')
movies_data_nested_list=[] # for storing movies_data_list
for i in range(0,len(category_boxes)):
    try:
        category_box=driver.find_elements(By.CLASS_NAME, 'swiper-box')[i]
    except IndexError: # usually happens when page failed to load
        driver.refresh()
        i-=1
        continue
    # position the element to make it not covered within viewport
    driver.execute_script('arguments[0].scrollIntoView();', category_box)
    driver.execute_script('window.scrollBy(0, -200)')
    category_name_box=category_box.find_element(By.CLASS_NAME, 'title-container')
    category_name=category_name_box.find_element(By.TAG_NAME, 'h2').text
    see_all_exists=True
    try:
        # check if a category has see more button
        see_all_button=category_name_box.find_element(By.CLASS_NAME, 'see-all')
    except NoSuchElementException:
        # this code run if a category has no see more button (has 20 movies or less)
        # it will scrape movies data directly
        see_all_exists=False
        j=0
        movies_by_category_box=category_box.find_element(By.CLASS_NAME, 'swiper-cont-overflow-visible')
        movies_by_category=movies_by_category_box.find_elements(By.CLASS_NAME, 'swiper-slide')
        next_button=movies_by_category_box.find_element(By.CLASS_NAME, 'swiper-button-next')
        for movie_by_category in movies_by_category:
            movies_data_list=[] # for storing page url, poster url, and category of a movie
            try:
                movie_poster_url=movie_by_category.find_element(By.CLASS_NAME, 'v-lazy-image-loaded').get_attribute('src')
            except:
                movie_poster_url=None
            # must hover on movie poster to unhide element that contains movie url
            hover_action=ActionChains(driver)
            hover_action.move_to_element(movie_by_category).perform()
            try:
                movie_page_url=movie_by_category.find_element(By.ID, 'G0').get_attribute('href')
            except NoSuchElementException:
                continue
            movies_data_list.append(movie_page_url)
            movies_data_list.append(category_name)
            movies_data_list.append(movie_poster_url)
            movies_data_nested_list.append(movies_data_list)
            print(j, movies_data_list) # for tracking webscraping progress
            # movies are displayed within horizontal container
            # click next button every 6 movies to show the next 6 movies
            j+=1
            if j%6==0 and len(movies_by_category)>6:
                next_button.click()
                sleep(1) # wait until animation is finished to avoid error
    # must not scrape from main page if a category has more than 20 movies
    # clicks see more button to navigate to another page that displays all movies within a category
    if see_all_exists:
        # due to animation, sometimes this button is covered by other element
        driver.execute_script('arguments[0].click();', see_all_button) # bypass covering element
        # load all movies by clicking load more button until all movies are loaded
        load_more_exists=True
        while load_more_exists:
            try:
                load_more=driver.find_element(By.CLASS_NAME, 'load-more')
                driver.execute_script('arguments[0].click();', load_more)
            except (NoSuchElementException, StaleElementReferenceException):
                load_more_exists=False
        movies_by_category=driver.find_elements(By.CLASS_NAME, 'content-item')
        j=0
        for movie_by_category in movies_by_category:
            movies_data_list=[] # for storing page url, poster url, and category of a movie
            # movies are displayed in grid view, 1 row contains 5 movies
            if j%5==0:
                # scroll down to make row that is being scraped visible
                driver.execute_script('arguments[0].scrollIntoView();', movie_by_category)
                driver.execute_script('window.scrollBy(0, -200)')
                sleep(1) # wait until animation is finished to avoid error
            try:
                movie_poster_url=movie_by_category.find_element(By.CLASS_NAME, 'v-lazy-image-loaded').get_attribute('src')
            except:
                movie_poster_url=None
            # must hover on movie poster to unhide element that contains movie url
            hover_action=ActionChains(driver)
            hover_action.move_to_element(movie_by_category).perform()
            movie_page_url=movie_by_category.find_element(By.ID, 'G0').get_attribute('href')
            movies_data_list.append(movie_page_url)
            movies_data_list.append(category_name)
            movies_data_list.append(movie_poster_url)
            movies_data_nested_list.append(movies_data_list)
            print(j, movies_data_list) # for tracking webscraping progress
            j+=1
        driver.back()
        sleep(4) # wait longer for main page to fully load to avoid error

# somehow the first attempt of using driver.get() to navigate from main page to a movie page will reload the main page instead
# however the second attempt works. this line is for overcoming this behavior
driver.get(movies_data_nested_list[0][0])

# scrape the rest of movie data by navigating to each movie page's url one by one
movies_data_dict_list=[] # for storing complete movie data
for i in range(0,len(movies_data_nested_list)):
    movies_data_dict={} # for storing complete movie data of a movie
    movies_data_dict['url']=movies_data_nested_list[i][0]
    movies_data_dict['category']=movies_data_nested_list[i][1]
    movies_data_dict['poster']=movies_data_nested_list[i][2]
    driver.get(movies_data_nested_list[i][0])
    sleep(4) # wait longer for movie page to fully load to avoid error
    try:
        title=driver.find_element(By.CSS_SELECTOR, 'h1.title').text
    except:
        title=None
    movies_data_dict['title']=title
    try:
        rating=driver.find_element(By.CSS_SELECTOR, '.box-age.text-center.rounded-borders').text
    except:
        rating=None
    movies_data_dict['rating']=rating
    try:
        duration=driver.find_element(By.CSS_SELECTOR, 'div.q-ml-md').text
    except:
        duration=None
    movies_data_dict['duration']=duration
    try:
        year_genre=driver.find_element(By.CSS_SELECTOR, 'div.text-weight-bold').text.split(' - ')
        movies_data_dict['year']=year_genre[0]
        movies_data_dict['genre']=year_genre[1]
    except:
        movies_data_dict['year']=None
        movies_data_dict['genre']=None
    try:
        language=driver.find_element(By.CSS_SELECTOR, 'div.text-italic').text
    except:
        language=None
    movies_data_dict['language']=language
    try:
        synopsis=driver.find_element(By.CSS_SELECTOR, 'p.box-synopsis').text
    except:
        synopsis=None
    movies_data_dict['synopsis']=synopsis
    try:
        director=driver.find_element(By.XPATH, '//div[contains( text( ), " Director : ")]/b').text
    except:
        director=None
    movies_data_dict['director']=director
    try:
        cast=driver.find_element(By.XPATH,
         '//div[contains( text( ), " Cast : ")]/b').text
    except:
        cast=None
    movies_data_dict['cast']=cast
    movies_data_dict_list.append(movies_data_dict)
    print(i, movies_data_dict, '\n') 

driver.quit()

movies_df=pd.DataFrame(movies_data_dict_list) # convert scraped data to a dataframe
# removes duplicates, usually happen when the page shows a single movies more than once
# some movies belong to more than 1 categories, this code doesn't count them as duplicates therefore they're kept
# they can be removed later if necessary
movies_df=movies_df.drop_duplicates()
movies_df.to_csv('visionplus.csv', index=False) # save to csv