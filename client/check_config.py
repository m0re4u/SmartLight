import yaml


def fix(pos, size, grid):
    for i in range(pos[0], pos[0]+size[0]):
        for j in range(pos[1], pos[1]+size[1]):
            if grid[j][i] == '0':
                grid[j][i] = 'X'
            else:
                grid[j][i] = '0'


if __name__ == '__main__':
    print(
        "Available lights are indicated by '.', unavailable lights are"
        " indicated by '0'\n\n"
        "lights directed by multiple modules are indicated with 'X'; fix those"
    )

    grid = [['.'] * 32 for _ in range(16)]

    with open('./config.yml') as f:
        config = yaml.load(f)
    for module in config['modules']:
        try:
            pos = config['modules'][module]['pos']
            size = config['modules'][module]['size']
            fix(pos, size, grid)
        except TypeError:
            for pair in config['modules'][module]:
                pos = pair['pos']
                size = pair['size']
                fix(pos, size, grid)

    for line in grid:
        print(' '.join(line))
