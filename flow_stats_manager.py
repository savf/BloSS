import sys


class FlowStatsManager():
    def __init__(self):
        '''
            Structures to keep port and flow statistics
        '''

        self.prev_stats_ports = defaultdict(lambda: defaultdict(lambda: None))
        self.prev_stats_flows = defaultdict(lambda: defaultdict(lambda: None))


def main():
    pass


if __name__ == "__main__":
    main()
