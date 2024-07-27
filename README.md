# ScooterInspector
Scrapper and analyzer of shared scooter data

The Bird API is given is based on the [WoBike](https://github.com/ubahnverleih/WoBike) repository.

To reproduce, the `BirdScrapper` class is used to get the data. 
The bird API is restricted to around 128 calls every few minutes, so that restricts the area possible without using a
list of proxies.

The `data_analysis` notebook can be used to create a video with heatmap distribution like given here:
![density_map_video.gif](density_map_video.gif)