import time

import requests

NO_CACHE_ENDPOINT = "http://localhost:3000/protected"
CACHE_ENDPOINT = "http://localhost:3000"
COUNT = 100


def main():
    cache_times = [0] * COUNT
    no_cache_times = [0] * COUNT
    avg1 = test_no_cache(no_cache_times)
    avg2 = test_cache(cache_times)
    print("Average time with cached requests: ", avg1)
    print("Average time without cached requests: ", avg2)


def test_no_cache(no_cache_times):
    for i in range(COUNT):
        start = time.time()
        requests.get(NO_CACHE_ENDPOINT)
        end = time.time()
        total = end - start
        no_cache_times[i] = total

    return mean(no_cache_times)


def test_cache(cache_times):
    for i in range(COUNT):
        start = time.time()
        requests.get(NO_CACHE_ENDPOINT)
        end = time.time()
        total = end - start
        cache_times[i] = total

    return mean(cache_times)


def mean(arr):
    return sum(arr) / len(arr)


if __name__ == "__main__":
    main()