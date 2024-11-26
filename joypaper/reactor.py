from dataclasses import dataclass
from typing import Callable, List
import random
import requests
import time
import base64


@dataclass
class Image:
    url: str
    file_type: str
    tags: List[str]
    width: int
    height: int


def filter_type(file_types):
    return lambda image: image.file_type in ["png", "jpeg"]


def filter_size(width, height):
    return lambda image: image.width >= width and image.height >= height


def filter_ratios(ratios, error=0.3):
    ratios = [r for r in ratios]

    def filter(image):
        ratio = image.width / image.height
        for r in ratios:
            if abs(r - ratio) / r < error:
                return True
        return False

    return filter


def get_default_filters(width, height):
    return [
        filter_type(["png", "jpeg"]),
        filter_size(width / 4, height / 2),
        filter_ratios([width / height, width / 4 / height]),
    ]


class Source:
    def __init__(self, logger, filters: List[Callable[[Image], bool]]):
        self.logger = logger
        self.filters = filters
        self.cache = []

    def get_image(self):
        while not self.cache:
            self.logger.debug("Requesting random posts")
            posts = self._get_more_posts()
            self.logger.debug(f"Got {len(posts)} posts")
            images = _extract_images(posts, self.logger)
            self.logger.debug(f"Got {len(images)} images")
            images = _filter_images(images, self.filters)
            self.logger.debug(f"Got {len(images)} suitable images")
            self.cache = images
        return self.cache.pop()

    def _get_more_posts(self):
        try:
            posts = _request_random_posts()
            return posts
        except Exception:
            self.logger.error("Error requesting posts", exc_info=True)
            self.logger.debug("Wait 10 seconds")
            time.sleep(10)
        return []


def _request_random_posts():
    # 1000 seems to be the limit
    page = random.randint(0, 1000)

    url = "https://api.joyreactor.cc/graphql"
    query = (
        """
      query MyQuery {
        search(query: "", showOnlyNsfw: true) {
          postPager {
            posts(page: """
        + str(page)
        + """) {
              attributes {
                ... on PostAttributePicture {
                  image {
                    height
                    width
                    type
                  }
                  id
                  post {
                    tags {
                      seoName
                    }
                  }
                }
              }
            }
          }
        }
      }
    """
    )

    response = requests.post(url, json={"query": query})

    if response.status_code != 200:
        raise RuntimeError("Bad response code: {}".format(response.status_code))

    data = response.json()

    posts = data["data"]["search"]["postPager"]["posts"]
    posts = [post["attributes"] for post in posts]

    return posts


def _get_url(image_id, tags, ftype):
    image_id = base64.b64decode(image_id).decode("utf-8")
    image_id = image_id.split(":")[1]
    tags = "-".join(tags[:3])

    return ("https://img10.joyreactor.cc/pics/post/full/" "{}-{}.{}").format(
        tags, image_id, ftype
    )


def _extract_images(posts, logger):
    images = []
    for post in posts:
        for attribute in post:
            try:
                file_type = attribute["image"]["type"].lower()
                tags = [tag["seoName"] for tag in attribute["post"]["tags"]]
                url = _get_url(attribute["id"], tags, file_type)
                images.append(
                    Image(
                        file_type=file_type,
                        height=attribute["image"]["height"],
                        width=attribute["image"]["width"],
                        tags=tags,
                        url=url,
                    )
                )
            except KeyError:
                logger.debug(f"Error parsing attribute {attribute}", exc_info=True)
                continue
    return images


def _filter_images(images, filters):
    ret = images
    for f in filters:
        ret = filter(f, ret)
    return list(ret)


random.seed()
