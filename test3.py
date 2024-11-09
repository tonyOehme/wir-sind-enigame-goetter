import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from tqdm import tqdm


def gather_words_from_file(file_path, word_length=None):
    """
    Gathers words from a text file.

    Parameters:
    - file_path (str): Path to the text file containing words.
    - word_length (int, optional): Length of the words to filter. If None, all words are included.

    Returns:
    - list: A list of words matching the criteria.
    """
    words_set = list()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            i = 0
            for line in f:
                word = line.strip()
                if word:
                    if word_length:
                        if len(word) == word_length:
                            if i < 100:
                                print(word)
                                i += 1
                            words_set.append(word)
                    else:
                        words_set.append(word)
                        if i < 100:
                            print(word)
                            i += 1
    except Exception as e:
        print(f"Error reading from file {file_path}: {e}")
        return []

    words_list = (list(words_set))
    return words_list


def send_post_request(word, task_id):
    """
    Sends a POST request for the given word.

    Parameters:
    - word (str): The word to send as the answer.

    Returns:
    - tuple: (word, response_dict) if successful.
    - tuple: (word, None) if an error occurs.
    """
    # Hardcoded Bearer Token
    token = ""  # your token

    # Headers as per the provided cURL command
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Content-Type': 'application/json',
        'Referer': 'https://www.enigame.de/hunt',
        'Origin': 'https://www.enigame.de',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Authorization': f'Bearer {token}',
        'Connection': 'keep-alive',
        'Cookie': (
            # your cookie
        ),
        'Priority': 'u=0',
        'TE': 'trailers',
    }

    url = 'https://www.enigame.de/api/user/query'

    payload = {
        "operationName": None,
        "variables": {
            "episodeTaskID": task_id,
            "answer": word
        },
        "query": """mutation checkAnswer($episodeTaskID: Int!, $answer: String!) {
  __typename
  checkAnswer(episodeTaskID: $episodeTaskID, answer: $answer) {
    __typename
    correct
    close
    currentEpisodeTask {
      __typename
      gid
      order
      task {
        __typename
        gid
        name
        content
        contentLink
      }
      startMessage {
        __typename
        content
        avatar {
          __typename
          code
        }
      }
      myProgression {
        __typename
        started
        solved
        etherPad
        unlockedEurekas {
          __typename
          id
          pattern
        }
        pauses {
          __typename
          begin
          end
        }
        lastAnswers {
          __typename
          text
          time
          user {
            __typename
            username
          }
        }
        closeAnswers {
          __typename
          text
          time
          user {
            __typename
            username
          }
        }
        displayAnswer
        finishSound {
          __typename
          code
        }
        hints {
          __typename
          totalHints
          nextHintAt
          unlockedHints {
            __typename
            id
            content
          }
          unlockedGroups {
            __typename
            id
            eurekas {
              __typename
              id
            }
            hints {
              __typename
              id
            }
          }
          unlockedVerificationForms {
            __typename
            id
            title
            header
            nextSubmitAt
            fields {
              __typename
              id
              name
              type
            }
          }
        }
      }
    }
    nextEpisodeID
    nextEpisodeTask {
      __typename
      gid
      order
      task {
        __typename
        gid
        name
        content
        contentLink
      }
      startMessage {
        __typename
        content
        avatar {
          __typename
          code
        }
      }
      myProgression {
        __typename
        started
        solved
        etherPad
        unlockedEurekas {
          __typename
          id
          pattern
        }
        pauses {
          __typename
          begin
          end
        }
        lastAnswers {
          __typename
          text
          time
          user {
            __typename
            username
          }
        }
        closeAnswers {
          __typename
          text
          time
          user {
            __typename
            username
          }
        }
        displayAnswer
        finishSound {
          __typename
          code
        }
        hints {
          __typename
          totalHints
          nextHintAt
          unlockedHints {
            __typename
            id
            content
          }
          unlockedGroups {
            __typename
            id
            eurekas {
              __typename
              id
            }
            hints {
              __typename
              id
            }
          }
          unlockedVerificationForms {
            __typename
            id
            title
            header
            nextSubmitAt
            fields {
              __typename
              id
              name
              type
            }
          }
        }
      }
    }
    rank
    rankSize
    rankSizeRange
    unlockedEureka {
      __typename
      id
      pattern
    }
  }
}"""
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.HTTPError as err:
        print(f"\nHTTP error occurred for word '{word}': {err}")
        print(f"Sentw word: {word}")
        time.sleep(1)
        return (word, None)
    except Exception as err:
        print(f"\nAn error occurred for word '{word}': {err}")
        return (word, None)

    try:
        return (word, response.json())
    except json.JSONDecodeError:
        print(f"\nFailed to parse JSON response for word '{word}'")
        print("Response content:", response.text)
        return (word, None)


def main():
    parser = argparse.ArgumentParser(
        description='Process a text file and send POST requests for each word.')
    parser.add_argument(
        'file', type=str, help='Path to the text file containing words.')
    parser.add_argument('--length', type=int, default=None,
                        help='Length of words to filter. If not specified, all words are included.')
    parser.add_argument('--output', type=str, default=None,
                        help='Optional output file to save responses.')
    parser.add_argument('--max_tries', type=int, default=None,
                        help='Maximum number of words to try.')
    parser.add_argument('--threads', type=int, default=1,
                        help='Number of threads to use for sending requests.')
    parser.add_argument('--task_id', type=int, default=1,
                        help='Number of threads to use for sending requests.')

    args = parser.parse_args()

    # Gather words from text file
    words = gather_words_from_file(args.file, word_length=args.length)

    if not words:
        print("No words to process. Exiting.")
        sys.exit(0)

    # Limit the number of words to max_tries if specified
    if args.max_tries:
        words = words[:args.max_tries]

    print(f"\nTotal words to process: {len(words)}")

    # Prepare to save responses if output file is specified
    output_lock = threading.Lock()
    if args.output:
        try:
            output_file = open(args.output, 'w', encoding='utf-8')
        except Exception as e:
            print(f"Error opening output file {args.output}: {e}")
            sys.exit(1)
    else:
        output_file = None

    # Progress bar
    progress_bar = tqdm(
        total=len(words), desc="Sending POST requests", unit="word")

    def task(word):
        result = send_post_request(word, args.task_id)
        if output_file and result[1]:
            with output_lock:
                try:
                    json.dump({result[0]: result[1]}, output_file)
                    output_file.write('\n')
                except Exception as e:
                    print(f"\nError writing response for word '{
                          result[0]}' to file: {e}")
        progress_bar.update(1)
        return result

    # Use ThreadPoolExecutor to send requests in parallel
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = [executor.submit(task, word) for word in words]
        # Optionally, you can process the results here if needed
        for future in as_completed(futures):
            pass  # Results are handled in the task function

    progress_bar.close()

    if output_file:
        output_file.close()
        print(f"\nAll responses have been saved to {args.output}")

    print("\nProcessing completed.")


if __name__ == "__main__":
    main()
