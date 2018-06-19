# Extract annotated screenshots of Facebook news feed

Files to collect synthetic screenshot data for training a machine learning model to visually identify Facebook ads.

Usage:

```
usage: python facebook_extract.py [-h] -d DIR -p PROFILEDIR
```
e.g.

```
facebook_extract.py -d c:\facebook_ad_dataset -p "c:\Users\[USERNAME]\AppData\Local\Google\Chrome\User Data\Default"
```

To visualize the dataset you can use visualize_data.py.

Usage:

```
python visualize_data.py [-h] -f FILE
```
Then use left/right arrows to navigate the dataset.
