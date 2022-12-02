import os
import pickle
import numpy as np
import logging
from matplotlib import pyplot as plt
from copy import deepcopy

# ---------------------------------------------------------------------------- #
#                               Helper Functions                               #
# ---------------------------------------------------------------------------- #
def plot_points_helper(points):
    '''Visualize points'''
    x, y = zip(*points)
    plt.scatter(x, y)
    plt.xticks(range(min(x), max(y)+1))
    plt.savefig("formation.png")

def wrapped_range(start, end, step=1):
    '''
    Returns a range that wraps around the grid
    '''
    if start < end:
        return list(range(start, end, step))
    else:
        return list(range(start, 100, step)) + list(range(0, end, step))

def wrap_point(x, y):
    '''
    Wrap the point around the grid
    '''
    return (x % 100, y % 100)

def get_neighbors(x, y, amoeba_map):
    neighbors = [wrap_point(x - 1, y), wrap_point(x + 1, y), wrap_point(x, y + 1), wrap_point(x, y - 1)]
    return [n for n in neighbors if amoeba_map[n[0]][n[1]] == 1]

def breaks_amoeba(point, amoeba_map):
    '''
    Returns whether or not the given point breaks the amoeba

    :param point: The point to check
    :param amoeba_map: The amoeba map
    :return: True if the point breaks the amoeba, False otherwise
    '''

    x, y = point
    # check that all amoeba cells are connected
    isolated_neighbors = get_neighbors(x, y, amoeba_map)
    queue = [isolated_neighbors[0]]
    copy_amoeba_map = deepcopy(amoeba_map)
    copy_amoeba_map[x][y] = 0
    visited = set()
    to_visit_isolated_connections = set(isolated_neighbors)
    while len(queue) > 0:
        cur_x, cur_y = queue.pop(0)
        if (cur_x, cur_y) in visited:
            continue
        if (cur_x, cur_y) in to_visit_isolated_connections:
            to_visit_isolated_connections.remove((cur_x, cur_y))
        visited.add((cur_x, cur_y))
        neighbors = get_neighbors(cur_x, cur_y, copy_amoeba_map)
        queue.extend(neighbors)
        if len(to_visit_isolated_connections) == 0:
            return False
    return True
    #TODO: make sure we don't need this code below? always true if break out of while loop?
    amoeba_cells = set([(i, j) for i, row in enumerate(copy_amoeba_map) for j, cell in enumerate(row) if cell != 0])
    return len(visited) != len(amoeba_cells) or len(visited - amoeba_cells) > 0

def remove_duplicates(points):
    validPoints = []
    addedPoints = set()
    for i, point in enumerate(points):
        if point not in addedPoints:
            validPoints.append(point)
            addedPoints.add(point)
    return validPoints
# ---------------------------------------------------------------------------- #
#                               Formation Classes                              #
# ---------------------------------------------------------------------------- #

class Formation:
    def __init__(self):
        self.phase = 0

    def update(self, phase):
        '''
        Update the formation based on the current info
        Must be called every turn to maintain the rules of the game
        '''
        self.phase = phase

    def get_all_retractable_points(self, goalFormation, state):
        '''
        Returns a list of all points that can be retracted that won't affect the goal formation
        
        :param goalFormation: The goal formation
        :param state: The current state
        :return: A list of all points that can be retracted
        '''
        canRetract = []
        amoebaMap = state.amoeba_map
        periphery = state.periphery
        for point in periphery:
            if point not in goalFormation:
                canRetract.append(point)

        return canRetract

    def get_moveable_points(self, moveablePoints, goalFormation, state):
        '''
        Returns a list of all points to move to to achieve the goal formation

        :param moveablePoints: The points that can be moved to
        :param goalFormation: The goal formation
        :param state: The current state
        :return: A list of all points to move to
        '''
        toMove = []
        amoebaMap = state.amoeba_map
        periphery = state.periphery
        # TODO: make this work? moveablePoints.sort(key=lambda point: self._dist_btwn_points(point, self._center_of_formation(goalFormation)))
        for point in moveablePoints:
            if point in goalFormation:
                toMove.append(point)
        return toMove

    def _dist_btwn_points(self, point1, point2):
        '''
        Returns the distance between two points

        :param point1: The first point
        :param point2: The second point
        :return: The distance between the two points
        '''
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _center_of_formation(self, formation):
        '''
        Returns the center of the formation

        :param formation: The formation
        :return: The center of the formation
        '''
        return (sum([point[0] for point in formation]) / len(formation), sum([point[1] for point in formation]) / len(formation))

    def get_n_moves(self, allRetracable, pointsToMoveTo, state, n_cells_can_move):
        ''' 
        Returns the points to retract and move so that len(pointsToMoveTo) == len(pointsToRetract)

        :param allRetracable: A list of all points that can be retracted
        :param pointsToMoveTo: A list of all points that need to be moved to
        :param state: The current state
        :param n_cells_can_move: The number of cells that can move based on the metabolism
        :return: A tuple of the points to retract and the points to move to
        '''
        amoebaMapCopy = deepcopy(state.amoeba_map)
        moveDups = [point for point in pointsToMoveTo if pointsToMoveTo.count(point) > 1]
        validPointsToMoveTo = [point for i, point in enumerate(pointsToMoveTo) if point not in moveDups and pointsToMoveTo.index(point) == i]
        allValidRetracable = []

        #make n passes? does this work
        for j in range(2):
            for i, point in enumerate(allRetracable):
                if point not in allValidRetracable and not breaks_amoeba(point, amoebaMapCopy):
                    allValidRetracable.append(point)
                    amoebaMapCopy[point[0]][point[1]] = 0

        allValidRetracable = allValidRetracable[:n_cells_can_move]
        validPointsToMoveTo = validPointsToMoveTo[:n_cells_can_move]

        if len(allValidRetracable) > len(validPointsToMoveTo):
            return allValidRetracable[:len(validPointsToMoveTo)], validPointsToMoveTo
        elif len(allValidRetracable) < len(validPointsToMoveTo):
            return allValidRetracable, validPointsToMoveTo[:len(allValidRetracable)]
        else:
            return allValidRetracable, validPointsToMoveTo

    def get_next_formation_points(self, state):
        '''
        Returns the next formation points

        :param state: The current state
        :return: A list of the next formation points
        '''
        raise NotImplementedError("Must be implemented by subclass")

    def get_phase(self, phase, state, retract, movable):
        '''
        Returns the current phase
        
        :param phase: The current phase
        :param state: The current state
        :param retract: The points to retract
        :param movable: The points to move to
        :return: The current phase
        '''
        raise NotImplementedError("Must be implemented by subclass")

class RakeFormation(Formation):
    def __init__(self):
        self.allPoints = []
        for y in range(50):
            self.allPoints.extend([(x, 50-y) for x in range(100)])
            self.allPoints.extend([(x, 50+y) for x in range(100)])

    def get_phase(self, phase, state, retract, movable):
        nCells = sum([sum(row) for row in state.amoeba_map])
        xStart, xEnd, yStart, yEnd = self._get_current_xy(state.amoeba_map)
        emptyCols = self._get_empty_cols_between(xStart, xEnd, state.amoeba_map)
        if phase == 0:
            phase = 0
        elif phase == 1:
            phase = 0
        if nCells > 466+6 and (phase == 1 or phase == 0):
            return 2
        elif phase == 2 and len(emptyCols) >= 90:
            return 3
        elif phase == 3 and  len(emptyCols) <= 6:
            return 2
        return phase

    def get_next_formation_points(self, state):
        nCells = sum([sum(row) for row in state.amoeba_map])
        amoebaMap = state.amoeba_map
        amoebaPoints = [(i, j) for i, row in enumerate(amoebaMap) for j, cell in enumerate(row) if cell == 1]

        #TODO: change ordering of moveable points
        #TODO: change ordering of retractable points, maybe based on distance to center of formation? mostly matters at the beginning
        if self.phase == 0:
            xStart, xEnd, yStart, yEnd = self._get_current_xy(amoebaMap)
            xOffset, yOffset = xStart, yStart

            previousPoints = self._get_formation(xOffset, yOffset, state, nCells)\
                + [(xOffset+i, 50) for i in range(0, 8)]\
                + self._get_formation(xOffset+8, yOffset, state, nCells)

            previousPoints = remove_duplicates(previousPoints)[:nCells]
            totalCorrectPoints = sum([1 for point in previousPoints if point in amoebaPoints])
            # print(xStart, xEnd, yStart, yEnd)
            # print("totalCorrectPoints: ", totalCorrectPoints)
            # print(len(previousPoints))
            if totalCorrectPoints < len(previousPoints)*0.99:#
                # print("Using prev formation")
                return previousPoints

            idealPoints = self._get_formation(xOffset+1, yOffset, state, nCells)\
                + [(xOffset+i, 50) for i in range(1, 9)]\
                + self._get_formation(xOffset+9, yOffset, state, nCells)

            idealPoints = remove_duplicates(idealPoints)
            return idealPoints
        elif self.phase == 1:
            xStart, xEnd, yStart, yEnd = self._get_current_xy(amoebaMap)
            xOffset, yOffset = xStart, yStart

            previousPoints = self._get_formation(xOffset, yOffset, state, nCells)\
                + [(xOffset+i, 50) for i in range(0, 8)]\
                + self._get_formation(xOffset+8, yOffset, state, nCells)

            previousPoints = remove_duplicates(previousPoints)[:nCells]
            totalCorrectPoints = sum([1 for point in previousPoints if point in amoebaPoints])
            # print(xStart, xEnd, yStart, yEnd)
            # print("totalCorrectPoints: ", totalCorrectPoints)
            # print(len(previousPoints))
            if totalCorrectPoints < len(previousPoints)*0.99:#
                # print("Using prev formation")
                return previousPoints

            idealPoints = self._get_formation(xOffset+1, yOffset, state, nCells)\
                + [(xOffset+i, 50) for i in range(1, 9)]\
                + self._get_formation(xOffset+9, yOffset, state, nCells)

            idealPoints = remove_duplicates(idealPoints)
            return idealPoints
        elif self.phase == 2:
            xStart, xEnd, yStart, yEnd = self._get_current_xy(amoebaMap)
            xOffset, yOffset = xStart, yStart #self._get_midpoint(yStart, yEnd)

            previousPoints = self._get_formation(xStart, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(xStart, xEnd-2)]\
                    + self._get_formation(xEnd-2, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(0, 100)]\

            previousPoints = remove_duplicates(previousPoints)[:nCells]
            totalCorrectPoints = sum([1 for point in previousPoints if point in amoebaPoints])
            # print(xStart, xEnd, yStart, yEnd)
            # print("totalCorrectPoints: ", totalCorrectPoints)
            # print(len(previousPoints))
            if totalCorrectPoints < len(previousPoints)*0.99:#
                # print("Using prev formation")
                previousPoints += self.allPoints
                previousPoints = remove_duplicates(previousPoints)[:nCells]
                return previousPoints
            idealPoints = self._get_formation(xStart-1, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(xStart, xEnd-1)]\
                    + self._get_formation(xEnd-1, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(0, 100)]\
                    + self.allPoints
            return idealPoints
        elif self.phase == 3:
            xStart, xEnd, yStart, yEnd = self._get_current_xy(amoebaMap)
            xOffset, yOffset = xStart, yStart #self._get_midpoint(yStart, yEnd)

            previousPoints = self._get_formation(xStart, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(xStart, xEnd-2)]\
                    + self._get_formation(xEnd-2, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(0, 100)]\

            previousPoints = remove_duplicates(previousPoints)[:nCells]
            totalCorrectPoints = sum([1 for point in previousPoints if point in amoebaPoints])
            # print(xStart, xEnd, yStart, yEnd)
            # print("totalCorrectPoints: ", totalCorrectPoints)
            # print(len(previousPoints))
            if totalCorrectPoints < len(previousPoints)*0.99:
                #TODO dont include all points in prevPoint and this calculation
                # print("Using prev formation")
                previousPoints += self.allPoints
                previousPoints = remove_duplicates(previousPoints)[:nCells]
                return previousPoints

            idealPoints = self._get_formation(xStart+1, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(xStart+1, xEnd-3)]\
                    + self._get_formation(xEnd-3, yOffset, state, nCells)\
                    + [(i, 50) for i in wrapped_range(0, 100)]\
                    + self.allPoints

            return idealPoints
            
            return idealPoints


        # Can have 4 phases (we use 2 bits of info)
        # Phase 0: get into formation/go forward
        # Phase 1: move down 1
        # Phase 2: 2 lines, move outwards
        # Phase 3: 2 lines move inwards
        raise NotImplementedError

    def _get_midpoint(self, start, end):
        if end < start:
            #TODO: 44 -> 3 = midpt of (100-44 + 3-0)//2 = 28
            return (100 - start + end - 0) // 2
        return (start + end) // 2

    def _get_current_xy(self, amoebaMap):
        '''
        Returns the current x and y offsets of the amoeba
        Assumes already in starting formation or moving

        :param amoebaMap: The amoeba map
        :return: A tuple of the start and end x and y
        '''
        #TODO change this all to be based on num cells in that row/col to account for random bacteria additions?
        # calculate n Cells then use that to calculate expected len of amoeba, use that to get the start end cols
        rowLens = [sum(amoebaMap[i]) for i in range(100)]
        cuttoff = max(rowLens) * 0.9
        rowsWithEntireLength = [x for x in range(100) if sum(amoebaMap[x]) >= cuttoff]

        cell_xs = [i for i, row in enumerate(amoebaMap) for j, cell in enumerate(row) if cell != 0]

        contiguousX = []
        cell_xs = sorted(list(set(cell_xs)))
        i = min(cell_xs)
        for x in cell_xs:
            if x != i:
                contiguousX = cell_xs[i:] + contiguousX
                break
            contiguousX.append(x)
            i += 1

        cell_ys = [j for i, row in enumerate(amoebaMap) for j, cell in enumerate(row) if cell != 0]
        contiguousY = []
        cell_ys = sorted(list(set(cell_ys)))
        i = min(cell_ys)
        for y in cell_ys:
            if y != i:
                contiguousY = cell_ys[i:] + contiguousY
                break
            contiguousY.append(y)
            i += 1
        contiguousXCopy = deepcopy(contiguousX)
        for x in contiguousXCopy:
            if x not in rowsWithEntireLength:
                contiguousX.remove(x)
            else:
                break
        contiguousXCopy = deepcopy(list(reversed(contiguousX)))
        for x in contiguousXCopy:
            if x not in rowsWithEntireLength:
                contiguousX.remove(x)
            else:
                break
        contiguousX.append((contiguousX[-1] + 1)%100)


        return contiguousX[0], contiguousX[-1], contiguousY[0], contiguousY[-1]

    def _get_empty_cols_between(self, start, end, amoebaMap):
        '''
        Returns the empty cols between the start and end

        :param start: The start cols (inclusive)
        :param end: The end cols (inclusive)
        :param amoebaMap: The amoeba map
        :return: list of indices of empty cols
        '''
        nCells = sum([sum(row) for row in amoebaMap])
        expectedLen = min(100, (3 * min(nCells // 7, 33)) % 100)
        emptyCols = []

        for i in wrapped_range(start, end+1):
            if sum(amoebaMap[i]) <= (3 * expectedLen/4):
                emptyCols.append(i)
        if len(emptyCols) == 0:
            return []

        continuousSeqs = {}
        for i in range(len(emptyCols)):
            if i == 0:
                continuousSeqs[emptyCols[i]] = 1
            else:
                if emptyCols[i] % 100 == (emptyCols[i-1] + 1) % 100:
                    continuousSeqs[emptyCols[i]] = continuousSeqs[emptyCols[i-1]] + 1
                else:
                    continuousSeqs[emptyCols[i]] = 1
                    
        longestSeq = []
        maxVal = max(continuousSeqs.values())
        if maxVal <= 1:
            print("No continuous seqs")
            return []
        idxOfMax = [k for k, v in continuousSeqs.items() if v == maxVal]
        modifiedIdxs = list(reversed(continuousSeqs.keys()))
        modifiedIdxs = modifiedIdxs[modifiedIdxs.index(idxOfMax[0]):]

        for i in modifiedIdxs:
            if i in continuousSeqs:
                longestSeq.insert(0, i)
            if continuousSeqs[i] == 1:
                break

        return longestSeq

    def _get_formation(self, x, yOffset, state, nCells):
        '''
        Returns the formation points for the given x and yOffset

        :param x: The x coordinate
        :param yOffset: The yOffset
        :param state: The current state
        :param nCells: The number of cells
        :return: A list of the formation points
        '''
        nChunks = min(nCells // 7, 33)
        formation = []
        for i in range(nChunks):
            formation += self._generate_chunk(x, yOffset)
            yOffset += 3
    
        # Add extra cells
        formation += self._generate_chunk(x, yOffset)[:nCells % 7]

        return formation

    def _generate_chunk(self, xOffset, yOffset):
        '''
        Generates a chunk of the formation
        |1|2|3|
        |4|5|
        |6|7|

        :param xOffset: The xOffset
        :param yOffset: The yOffset
        :return: A list of the chunk points
        '''
        chunk = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
        return [wrap_point(x + xOffset, y + yOffset) for x, y in chunk]

class SpaceCurveFormation(Formation):

    def __init__(self):
        self.all_points = [(49, 50), (50, 50), (50, 49), (49, 49), (48, 50), (48, 49), (49, 51), (49, 48), (50, 51), (50, 48), (51, 50), (51, 49), (51, 51), (51, 48), (48, 48), (48, 51), (52, 51), (51, 47), (47, 48), (48, 52), (53, 51), (51, 46), (46, 48), (48, 53), (54, 51), (51, 45), (45, 48), (48, 54), (54, 52), (52, 45), (45, 47), (47, 54), (54, 53), (53, 45), (45, 46), (46, 54), (54, 54), (54, 45), (45, 45), (45, 54), (53, 54), (54, 46), (46, 45), (45, 53), (52, 54), (54, 47), (47, 45), (45, 52), (51, 54), (54, 48), (48, 45), (45, 51), (51, 55), (55, 48), (48, 44), (44, 51), (51, 56), (56, 48), (48, 43), (43, 51), (51, 57), (57, 48), (48, 42), (42, 51), (51, 58), (58, 48), (48, 41), (41, 51), (51, 59), (59, 48), (48, 40), (40, 51), (51, 60), (60, 48), (48, 39), (39, 51), (52, 60), (60, 47), (47, 39), (39, 52), (53, 60), (60, 46), (46, 39), (39, 53), (54, 60), (60, 45), (45, 39), (39, 54), (54, 59), (59, 45), (45, 40), (40, 54), (54, 58), (58, 45), (45, 41), (41, 54), (54, 57), (57, 45), (45, 42), (42, 54), (55, 57), (57, 44), (44, 42), (42, 55), (56, 57), (57, 43), (43, 42), (42, 56), (57, 57), (57, 42), (42, 42), (42, 57), (57, 58), (58, 42), (42, 41), (41, 57), (57, 59), (59, 42), (42, 40), (40, 57), (57, 60), (60, 42), (42, 39), (39, 57), (58, 60), (60, 41), (41, 39), (39, 58), (59, 60), (60, 40), (40, 39), (39, 59), (60, 60), (60, 39), (39, 39), (39, 60), (60, 59), (59, 39), (39, 40), (40, 60), (60, 58), (58, 39), (39, 41), (41, 60), (60, 57), (57, 39), (39, 42), (42, 60), (60, 56), (56, 39), (39, 43), (43, 60), (60, 55), (55, 39), (39, 44), (44, 60), (60, 54), (54, 39), (39, 45), (45, 60), (59, 54), (54, 40), (40, 45), (45, 59), (58, 54), (54, 41), (41, 45), (45, 58), (57, 54), (54, 42), (42, 45), (45, 57), (57, 53), (53, 42), (42, 46), (46, 57), (57, 52), (52, 42), (42, 47), (47, 57), (57, 51), (51, 42), (42, 48), (48, 57), (58, 51), (51, 41), (41, 48), (48, 58), (59, 51), (51, 40), (40, 48), (48, 59), (60, 51), (51, 39), (39, 48), (48, 60), (61, 51), (51, 38), (38, 48), (48, 61), (62, 51), (51, 37), (37, 48), (48, 62), (63, 51), (51, 36), (36, 48), (48, 63), (63, 52), (52, 36), (36, 47), (47, 63), (63, 53), (53, 36), (36, 46), (46, 63), (63, 54), (54, 36), (36, 45), (45, 63), (64, 54), (54, 35), (35, 45), (45, 64), (65, 54), (54, 34), (34, 45), (45, 65), (66, 54), (54, 33), (33, 45), (45, 66), (66, 53), (53, 33), (33, 46), (46, 66), (66, 52), (52, 33), (33, 47), (47, 66), (66, 51), (51, 33), (33, 48), (48, 66), (67, 51), (51, 32), (32, 48), (48, 67), (68, 51), (51, 31), (31, 48), (48, 68), (69, 51), (51, 30), (30, 48), (48, 69), (70, 51), (51, 29), (29, 48), (48, 70), (71, 51), (51, 28), (28, 48), (48, 71), (72, 51), (51, 27), (27, 48), (48, 72), (72, 52), (52, 27), (27, 47), (47, 72), (72, 53), (53, 27), (27, 46), (46, 72), (72, 54), (54, 27), (27, 45), (45, 72), (71, 54), (54, 28), (28, 45), (45, 71), (70, 54), (54, 29), (29, 45), (45, 70), (69, 54), (54, 30), (30, 45), (45, 69), (69, 55), (55, 30), (30, 44), (44, 69), (69, 56), (56, 30), (30, 43), (43, 69), (69, 57), (57, 30), (30, 42), (42, 69), (70, 57), (57, 29), (29, 42), (42, 70), (71, 57), (57, 28), (28, 42), (42, 71), (72, 57), (57, 27), (27, 42), (42, 72), (72, 58), (58, 27), (27, 41), (41, 72), (72, 59), (59, 27), (27, 40), (40, 72), (72, 60), (60, 27), (27, 39), (39, 72), (71, 60), (60, 28), (28, 39), (39, 71), (70, 60), (60, 29), (29, 39), (39, 70), (69, 60), (60, 30), (30, 39), (39, 69), (68, 60), (60, 31), (31, 39), (39, 68), (67, 60), (60, 32), (32, 39), (39, 67), (66, 60), (60, 33), (33, 39), (39, 66), (66, 59), (59, 33), (33, 40), (40, 66), (66, 58), (58, 33), (33, 41), (41, 66), (66, 57), (57, 33), (33, 42), (42, 66), (65, 57), (57, 34), (34, 42), (42, 65), (64, 57), (57, 35), (35, 42), (42, 64), (63, 57), (57, 36), (36, 42), (42, 63), (63, 58), (58, 36), (36, 41), (41, 63), (63, 59), (59, 36), (36, 40), (40, 63), (63, 60), (60, 36), (36, 39), (39, 63), (63, 61), (61, 36), (36, 38), (38, 63), (63, 62), (62, 36), (36, 37), (37, 63), (63, 63), (63, 36), (36, 36), (36, 63), (63, 64), (64, 36), (36, 35), (35, 63), (63, 65), (65, 36), (36, 34), (34, 63), (63, 66), (66, 36), (36, 33), (33, 63), (64, 66), (66, 35), (35, 33), (33, 64), (65, 66), (66, 34), (34, 33), (33, 65), (66, 66), (66, 33), (33, 33), (33, 66), (66, 65), (65, 33), (33, 34), (34, 66), (66, 64), (64, 33), (33, 35), (35, 66), (66, 63), (63, 33), (33, 36), (36, 66), (67, 63), (63, 32), (32, 36), (36, 67), (68, 63), (63, 31), (31, 36), (36, 68), (69, 63), (63, 30), (30, 36), (36, 69), (70, 63), (63, 29), (29, 36), (36, 70), (71, 63), (63, 28), (28, 36), (36, 71), (72, 63), (63, 27), (27, 36), (36, 72), (72, 64), (64, 27), (27, 35), (35, 72), (72, 65), (65, 27), (27, 34), (34, 72), (72, 66), (66, 27), (27, 33), (33, 72), (71, 66), (66, 28), (28, 33), (33, 71), (70, 66), (66, 29), (29, 33), (33, 70), (69, 66), (66, 30), (30, 33), (33, 69), (69, 67), (67, 30), (30, 32), (32, 69), (69, 68), (68, 30), (30, 31), (31, 69), (69, 69), (69, 30), (30, 30), (30, 69), (70, 69), (69, 29), (29, 30), (30, 70), (71, 69), (69, 28), (28, 30), (30, 71), (72, 69), (69, 27), (27, 30), (30, 72), (72, 70), (70, 27), (27, 29), (29, 72), (72, 71), (71, 27), (27, 28), (28, 72), (72, 72), (72, 27), (27, 27), (27, 72), (71, 72), (72, 28), (28, 27), (27, 71), (70, 72), (72, 29), (29, 27), (27, 70), (69, 72), (72, 30), (30, 27), (27, 69), (68, 72), (72, 31), (31, 27), (27, 68), (67, 72), (72, 32), (32, 27), (27, 67), (66, 72), (72, 33), (33, 27), (27, 66), (66, 71), (71, 33), (33, 28), (28, 66), (66, 70), (70, 33), (33, 29), (29, 66), (66, 69), (69, 33), (33, 30), (30, 66), (65, 69), (69, 34), (34, 30), (30, 65), (64, 69), (69, 35), (35, 30), (30, 64), (63, 69), (69, 36), (36, 30), (30, 63), (63, 70), (70, 36), (36, 29), (29, 63), (63, 71), (71, 36), (36, 28), (28, 63), (63, 72), (72, 36), (36, 27), (27, 63), (62, 72), (72, 37), (37, 27), (27, 62), (61, 72), (72, 38), (38, 27), (27, 61), (60, 72), (72, 39), (39, 27), (27, 60), (59, 72), (72, 40), (40, 27), (27, 59), (58, 72), (72, 41), (41, 27), (27, 58), (57, 72), (72, 42), (42, 27), (27, 57), (57, 71), (71, 42), (42, 28), (28, 57), (57, 70), (70, 42), (42, 29), (29, 57), (57, 69), (69, 42), (42, 30), (30, 57), (58, 69), (69, 41), (41, 30), (30, 58), (59, 69), (69, 40), (40, 30), (30, 59), (60, 69), (69, 39), (39, 30), (30, 60), (60, 68), (68, 39), (39, 31), (31, 60), (60, 67), (67, 39), (39, 32), (32, 60), (60, 66), (66, 39), (39, 33), (33, 60), (60, 65), (65, 39), (39, 34), (34, 60), (60, 64), (64, 39), (39, 35), (35, 60), (60, 63), (63, 39), (39, 36), (36, 60), (59, 63), (63, 40), (40, 36), (36, 59), (58, 63), (63, 41), (41, 36), (36, 58), (57, 63), (63, 42), (42, 36), (36, 57), (57, 64), (64, 42), (42, 35), (35, 57), (57, 65), (65, 42), (42, 34), (34, 57), (57, 66), (66, 42), (42, 33), (33, 57), (56, 66), (66, 43), (43, 33), (33, 56), (55, 66), (66, 44), (44, 33), (33, 55), (54, 66), (66, 45), (45, 33), (33, 54), (54, 65), (65, 45), (45, 34), (34, 54), (54, 64), (64, 45), (45, 35), (35, 54), (54, 63), (63, 45), (45, 36), (36, 54), (53, 63), (63, 46), (46, 36), (36, 53), (52, 63), (63, 47), (47, 36), (36, 52), (51, 63), (63, 48), (48, 36), (36, 51), (51, 64), (64, 48), (48, 35), (35, 51), (51, 65), (65, 48), (48, 34), (34, 51), (51, 66), (66, 48), (48, 33), (33, 51), (51, 67), (67, 48), (48, 32), (32, 51), (51, 68), (68, 48), (48, 31), (31, 51), (51, 69), (69, 48), (48, 30), (30, 51), (52, 69), (69, 47), (47, 30), (30, 52), (53, 69), (69, 46), (46, 30), (30, 53), (54, 69), (69, 45), (45, 30), (30, 54), (54, 70), (70, 45), (45, 29), (29, 54), (54, 71), (71, 45), (45, 28), (28, 54), (54, 72), (72, 45), (45, 27), (27, 54), (53, 72), (72, 46), (46, 27), (27, 53), (52, 72), (72, 47), (47, 27), (27, 52), (51, 72), (72, 48), (48, 27), (27, 51), (51, 73), (73, 48), (48, 26), (26, 51), (51, 74), (74, 48), (48, 25), (25, 51), (51, 75), (75, 48), (48, 24), (24, 51), (51, 76), (76, 48), (48, 23), (23, 51), (51, 77), (77, 48), (48, 22), (22, 51), (51, 78), (78, 48), (48, 21), (21, 51), (52, 78), (78, 47), (47, 21), (21, 52), (53, 78), (78, 46), (46, 21), (21, 53), (54, 78), (78, 45), (45, 21), (21, 54), (54, 77), (77, 45), (45, 22), (22, 54), (54, 76), (76, 45), (45, 23), (23, 54), (54, 75), (75, 45), (45, 24), (24, 54), (55, 75), (75, 44), (44, 24), (24, 55), (56, 75), (75, 43), (43, 24), (24, 56), (57, 75), (75, 42), (42, 24), (24, 57), (58, 75), (75, 41), (41, 24), (24, 58), (59, 75), (75, 40), (40, 24), (24, 59), (60, 75), (75, 39), (39, 24), (24, 60), (60, 76), (76, 39), (39, 23), (23, 60), (60, 77), (77, 39), (39, 22), (22, 60), (60, 78), (78, 39), (39, 21), (21, 60), (59, 78), (78, 40), (40, 21), (21, 59), (58, 78), (78, 41), (41, 21), (21, 58), (57, 78), (78, 42), (42, 21), (21, 57), (57, 79), (79, 42), (42, 20), (20, 57), (57, 80), (80, 42), (42, 19), (19, 57), (57, 81), (81, 42), (42, 18), (18, 57), (58, 81), (81, 41), (41, 18), (18, 58), (59, 81), (81, 40), (40, 18), (18, 59), (60, 81), (81, 39), (39, 18), (18, 60), (60, 82), (82, 39), (39, 17), (17, 60), (60, 83), (83, 39), (39, 16), (16, 60), (60, 84), (84, 39), (39, 15), (15, 60), (59, 84), (84, 40), (40, 15), (15, 59), (58, 84), (84, 41), (41, 15), (15, 58), (57, 84), (84, 42), (42, 15), (15, 57), (56, 84), (84, 43), (43, 15), (15, 56), (55, 84), (84, 44), (44, 15), (15, 55), (54, 84), (84, 45), (45, 15), (15, 54), (54, 83), (83, 45), (45, 16), (16, 54), (54, 82), (82, 45), (45, 17), (17, 54), (54, 81), (81, 45), (45, 18), (18, 54), (53, 81), (81, 46), (46, 18), (18, 53), (52, 81), (81, 47), (47, 18), (18, 52), (51, 81), (81, 48), (48, 18), (18, 51), (51, 82), (82, 48), (48, 17), (17, 51), (51, 83), (83, 48), (48, 16), (16, 51), (51, 84), (84, 48), (48, 15), (15, 51), (51, 85), (85, 48), (48, 14), (14, 51), (51, 86), (86, 48), (48, 13), (13, 51), (51, 87), (87, 48), (48, 12), (12, 51), (52, 87), (87, 47), (47, 12), (12, 52), (53, 87), (87, 46), (46, 12), (12, 53), (54, 87), (87, 45), (45, 12), (12, 54), (54, 88), (88, 45), (45, 11), (11, 54), (54, 89), (89, 45), (45, 10), (10, 54), (54, 90), (90, 45), (45, 9), (9, 54), (53, 90), (90, 46), (46, 9), (9, 53), (52, 90), (90, 47), (47, 9), (9, 52), (51, 90), (90, 48), (48, 9), (9, 51), (51, 91), (91, 48), (48, 8), (8, 51), (51, 92), (92, 48), (48, 7), (7, 51), (51, 93), (93, 48), (48, 6), (6, 51), (51, 94), (94, 48), (48, 5), (5, 51), (51, 95), (95, 48), (48, 4), (4, 51), (51, 96), (96, 48), (48, 3), (3, 51), (52, 96), (96, 47), (47, 3), (3, 52), (53, 96), (96, 46), (46, 3), (3, 53), (54, 96), (96, 45), (45, 3), (3, 54), (54, 95), (95, 45), (45, 4), (4, 54), (54, 94), (94, 45), (45, 5), (5, 54), (54, 93), (93, 45), (45, 6), (6, 54), (55, 93), (93, 44), (44, 6), (6, 55), (56, 93), (93, 43), (43, 6), (6, 56), (57, 93), (93, 42), (42, 6), (6, 57), (57, 94), (94, 42), (42, 5), (5, 57), (57, 95), (95, 42), (42, 4), (4, 57), (57, 96), (96, 42), (42, 3), (3, 57), (58, 96), (96, 41), (41, 3), (3, 58), (59, 96), (96, 40), (40, 3), (3, 59), (60, 96), (96, 39), (39, 3), (3, 60), (60, 95), (95, 39), (39, 4), (4, 60), (60, 94), (94, 39), (39, 5), (5, 60), (60, 93), (93, 39), (39, 6), (6, 60), (60, 92), (92, 39), (39, 7), (7, 60), (60, 91), (91, 39), (39, 8), (8, 60), (60, 90), (90, 39), (39, 9), (9, 60), (59, 90), (90, 40), (40, 9), (9, 59), (58, 90), (90, 41), (41, 9), (9, 58), (57, 90), (90, 42), (42, 9), (9, 57), (57, 89), (89, 42), (42, 10), (10, 57), (57, 88), (88, 42), (42, 11), (11, 57), (57, 87), (87, 42), (42, 12), (12, 57), (58, 87), (87, 41), (41, 12), (12, 58), (59, 87), (87, 40), (40, 12), (12, 59), (60, 87), (87, 39), (39, 12), (12, 60), (61, 87), (87, 38), (38, 12), (12, 61), (62, 87), (87, 37), (37, 12), (12, 62), (63, 87), (87, 36), (36, 12), (12, 63), (64, 87), (87, 35), (35, 12), (12, 64), (65, 87), (87, 34), (34, 12), (12, 65), (66, 87), (87, 33), (33, 12), (12, 66), (66, 88), (88, 33), (33, 11), (11, 66), (66, 89), (89, 33), (33, 10), (10, 66), (66, 90), (90, 33), (33, 9), (9, 66), (65, 90), (90, 34), (34, 9), (9, 65), (64, 90), (90, 35), (35, 9), (9, 64), (63, 90), (90, 36), (36, 9), (9, 63), (63, 91), (91, 36), (36, 8), (8, 63), (63, 92), (92, 36), (36, 7), (7, 63), (63, 93), (93, 36), (36, 6), (6, 63), (63, 94), (94, 36), (36, 5), (5, 63), (63, 95), (95, 36), (36, 4), (4, 63), (63, 96), (96, 36), (36, 3), (3, 63), (64, 96), (96, 35), (35, 3), (3, 64), (65, 96), (96, 34), (34, 3), (3, 65), (66, 96), (96, 33), (33, 3), (3, 66), (66, 95), (95, 33), (33, 4), (4, 66), (66, 94), (94, 33), (33, 5), (5, 66), (66, 93), (93, 33), (33, 6), (6, 66), (67, 93), (93, 32), (32, 6), (6, 67), (68, 93), (93, 31), (31, 6), (6, 68), (69, 93), (93, 30), (30, 6), (6, 69), (69, 94), (94, 30), (30, 5), (5, 69), (69, 95), (95, 30), (30, 4), (4, 69), (69, 96), (96, 30), (30, 3), (3, 69), (70, 96), (96, 29), (29, 3), (3, 70), (71, 96), (96, 28), (28, 3), (3, 71), (72, 96), (96, 27), (27, 3), (3, 72), (72, 95), (95, 27), (27, 4), (4, 72), (72, 94), (94, 27), (27, 5), (5, 72), (72, 93), (93, 27), (27, 6), (6, 72), (72, 92), (92, 27), (27, 7), (7, 72), (72, 91), (91, 27), (27, 8), (8, 72), (72, 90), (90, 27), (27, 9), (9, 72), (71, 90), (90, 28), (28, 9), (9, 71), (70, 90), (90, 29), (29, 9), (9, 70), (69, 90), (90, 30), (30, 9), (9, 69), (69, 89), (89, 30), (30, 10), (10, 69), (69, 88), (88, 30), (30, 11), (11, 69), (69, 87), (87, 30), (30, 12), (12, 69), (70, 87), (87, 29), (29, 12), (12, 70), (71, 87), (87, 28), (28, 12), (12, 71), (72, 87), (87, 27), (27, 12), (12, 72), (72, 86), (86, 27), (27, 13), (13, 72), (72, 85), (85, 27), (27, 14), (14, 72), (72, 84), (84, 27), (27, 15), (15, 72), (72, 83), (83, 27), (27, 16), (16, 72), (72, 82), (82, 27), (27, 17), (17, 72), (72, 81), (81, 27), (27, 18), (18, 72), (71, 81), (81, 28), (28, 18), (18, 71), (70, 81), (81, 29), (29, 18), (18, 70), (69, 81), (81, 30), (30, 18), (18, 69), (69, 82), (82, 30), (30, 17), (17, 69), (69, 83), (83, 30), (30, 16), (16, 69), (69, 84), (84, 30), (30, 15), (15, 69), (68, 84), (84, 31), (31, 15), (15, 68), (67, 84), (84, 32), (32, 15), (15, 67), (66, 84), (84, 33), (33, 15), (15, 66), (65, 84), (84, 34), (34, 15), (15, 65), (64, 84), (84, 35), (35, 15), (15, 64), (63, 84), (84, 36), (36, 15), (15, 63), (63, 83), (83, 36), (36, 16), (16, 63), (63, 82), (82, 36), (36, 17), (17, 63), (63, 81), (81, 36), (36, 18), (18, 63), (64, 81), (81, 35), (35, 18), (18, 64), (65, 81), (81, 34), (34, 18), (18, 65), (66, 81), (81, 33), (33, 18), (18, 66), (66, 80), (80, 33), (33, 19), (19, 66), (66, 79), (79, 33), (33, 20), (20, 66), (66, 78), (78, 33), (33, 21), (21, 66), (65, 78), (78, 34), (34, 21), (21, 65), (64, 78), (78, 35), (35, 21), (21, 64), (63, 78), (78, 36), (36, 21), (21, 63), (63, 77), (77, 36), (36, 22), (22, 63), (63, 76), (76, 36), (36, 23), (23, 63), (63, 75), (75, 36), (36, 24), (24, 63), (64, 75), (75, 35), (35, 24), (24, 64), (65, 75), (75, 34), (34, 24), (24, 65), (66, 75), (75, 33), (33, 24), (24, 66), (67, 75), (75, 32), (32, 24), (24, 67), (68, 75), (75, 31), (31, 24), (24, 68), (69, 75), (75, 30), (30, 24), (24, 69), (69, 76), (76, 30), (30, 23), (23, 69), (69, 77), (77, 30), (30, 22), (22, 69), (69, 78), (78, 30), (30, 21), (21, 69), (70, 78), (78, 29), (29, 21), (21, 70), (71, 78), (78, 28), (28, 21), (21, 71), (72, 78), (78, 27), (27, 21), (21, 72), (72, 77), (77, 27), (27, 22), (22, 72), (72, 76), (76, 27), (27, 23), (23, 72), (72, 75), (75, 27), (27, 24), (24, 72), (73, 75), (75, 26), (26, 24), (24, 73), (74, 75), (75, 25), (25, 24), (24, 74), (75, 75), (75, 24), (24, 24), (24, 75), (75, 76), (76, 24), (24, 23), (23, 75), (75, 77), (77, 24), (24, 22), (22, 75), (75, 78), (78, 24), (24, 21), (21, 75), (76, 78), (78, 23), (23, 21), (21, 76), (77, 78), (78, 22), (22, 21), (21, 77), (78, 78), (78, 21), (21, 21), (21, 78), (78, 77), (77, 21), (21, 22), (22, 78), (78, 76), (76, 21), (21, 23), (23, 78), (78, 75), (75, 21), (21, 24), (24, 78), (79, 75), (75, 20), (20, 24), (24, 79), (80, 75), (75, 19), (19, 24), (24, 80), (81, 75), (75, 18), (18, 24), (24, 81), (82, 75), (75, 17), (17, 24), (24, 82), (83, 75), (75, 16), (16, 24), (24, 83), (84, 75), (75, 15), (15, 24), (24, 84), (84, 76), (76, 15), (15, 23), (23, 84), (84, 77), (77, 15), (15, 22), (22, 84), (84, 78), (78, 15), (15, 21), (21, 84), (83, 78), (78, 16), (16, 21), (21, 83), (82, 78), (78, 17), (17, 21), (21, 82), (81, 78), (78, 18), (18, 21), (21, 81), (81, 79), (79, 18), (18, 20), (20, 81), (81, 80), (80, 18), (18, 19), (19, 81), (81, 81), (81, 18), (18, 18), (18, 81), (82, 81), (81, 17), (17, 18), (18, 82), (83, 81), (81, 16), (16, 18), (18, 83), (84, 81), (81, 15), (15, 18), (18, 84), (84, 82), (82, 15), (15, 17), (17, 84), (84, 83), (83, 15), (15, 16), (16, 84), (84, 84), (84, 15), (15, 15), (15, 84), (83, 84), (84, 16), (16, 15), (15, 83), (82, 84), (84, 17), (17, 15), (15, 82), (81, 84), (84, 18), (18, 15), (15, 81), (80, 84), (84, 19), (19, 15), (15, 80), (79, 84), (84, 20), (20, 15), (15, 79), (78, 84), (84, 21), (21, 15), (15, 78), (78, 83), (83, 21), (21, 16), (16, 78), (78, 82), (82, 21), (21, 17), (17, 78), (78, 81), (81, 21), (21, 18), (18, 78), (77, 81), (81, 22), (22, 18), (18, 77), (76, 81), (81, 23), (23, 18), (18, 76), (75, 81), (81, 24), (24, 18), (18, 75), (75, 82), (82, 24), (24, 17), (17, 75), (75, 83), (83, 24), (24, 16), (16, 75), (75, 84), (84, 24), (24, 15), (15, 75), (75, 85), (85, 24), (24, 14), (14, 75), (75, 86), (86, 24), (24, 13), (13, 75), (75, 87), (87, 24), (24, 12), (12, 75), (76, 87), (87, 23), (23, 12), (12, 76), (77, 87), (87, 22), (22, 12), (12, 77), (78, 87), (87, 21), (21, 12), (12, 78), (78, 88), (88, 21), (21, 11), (11, 78), (78, 89), (89, 21), (21, 10), (10, 78), (78, 90), (90, 21), (21, 9), (9, 78), (77, 90), (90, 22), (22, 9), (9, 77), (76, 90), (90, 23), (23, 9), (9, 76), (75, 90), (90, 24), (24, 9), (9, 75), (75, 91), (91, 24), (24, 8), (8, 75), (75, 92), (92, 24), (24, 7), (7, 75), (75, 93), (93, 24), (24, 6), (6, 75), (75, 94), (94, 24), (24, 5), (5, 75), (75, 95), (95, 24), (24, 4), (4, 75), (75, 96), (96, 24), (24, 3), (3, 75), (76, 96), (96, 23), (23, 3), (3, 76), (77, 96), (96, 22), (22, 3), (3, 77), (78, 96), (96, 21), (21, 3), (3, 78), (78, 95), (95, 21), (21, 4), (4, 78), (78, 94), (94, 21), (21, 5), (5, 78), (78, 93), (93, 21), (21, 6), (6, 78), (79, 93), (93, 20), (20, 6), (6, 79), (80, 93), (93, 19), (19, 6), (6, 80), (81, 93), (93, 18), (18, 6), (6, 81), (81, 94), (94, 18), (18, 5), (5, 81), (81, 95), (95, 18), (18, 4), (4, 81), (81, 96), (96, 18), (18, 3), (3, 81), (82, 96), (96, 17), (17, 3), (3, 82), (83, 96), (96, 16), (16, 3), (3, 83), (84, 96), (96, 15), (15, 3), (3, 84), (84, 95), (95, 15), (15, 4), (4, 84), (84, 94), (94, 15), (15, 5), (5, 84), (84, 93), (93, 15), (15, 6), (6, 84), (84, 92), (92, 15), (15, 7), (7, 84), (84, 91), (91, 15), (15, 8), (8, 84), (84, 90), (90, 15), (15, 9), (9, 84), (83, 90), (90, 16), (16, 9), (9, 83), (82, 90), (90, 17), (17, 9), (9, 82), (81, 90), (90, 18), (18, 9), (9, 81), (81, 89), (89, 18), (18, 10), (10, 81), (81, 88), (88, 18), (18, 11), (11, 81), (81, 87), (87, 18), (18, 12), (12, 81), (82, 87), (87, 17), (17, 12), (12, 82), (83, 87), (87, 16), (16, 12), (12, 83), (84, 87), (87, 15), (15, 12), (12, 84), (85, 87), (87, 14), (14, 12), (12, 85), (86, 87), (87, 13), (13, 12), (12, 86), (87, 87), (87, 12), (12, 12), (12, 87), (88, 87), (87, 11), (11, 12), (12, 88), (89, 87), (87, 10), (10, 12), (12, 89), (90, 87), (87, 9), (9, 12), (12, 90), (90, 88), (88, 9), (9, 11), (11, 90), (90, 89), (89, 9), (9, 10), (10, 90), (90, 90), (90, 9), (9, 9), (9, 90), (89, 90), (90, 10), (10, 9), (9, 89), (88, 90), (90, 11), (11, 9), (9, 88), (87, 90), (90, 12), (12, 9), (9, 87), (87, 91), (91, 12), (12, 8), (8, 87), (87, 92), (92, 12), (12, 7), (7, 87), (87, 93), (93, 12), (12, 6), (6, 87), (87, 94), (94, 12), (12, 5), (5, 87), (87, 95), (95, 12), (12, 4), (4, 87), (87, 96), (96, 12), (12, 3), (3, 87), (88, 96), (96, 11), (11, 3), (3, 88), (89, 96), (96, 10), (10, 3), (3, 89), (90, 96), (96, 9), (9, 3), (3, 90), (90, 95), (95, 9), (9, 4), (4, 90), (90, 94), (94, 9), (9, 5), (5, 90), (90, 93), (93, 9), (9, 6), (6, 90), (91, 93), (93, 8), (8, 6), (6, 91), (92, 93), (93, 7), (7, 6), (6, 92), (93, 93), (93, 6), (6, 6), (6, 93), (93, 94), (94, 6), (6, 5), (5, 93), (93, 95), (95, 6), (6, 4), (4, 93), (93, 96), (96, 6), (6, 3), (3, 93), (94, 96), (96, 5), (5, 3), (3, 94), (95, 96), (96, 4), (4, 3), (3, 95), (96, 96), (96, 3), (3, 3), (3, 96), (96, 95), (95, 3), (3, 4), (4, 96), (96, 94), (94, 3), (3, 5), (5, 96), (96, 93), (93, 3), (3, 6), (6, 96), (96, 92), (92, 3), (3, 7), (7, 96), (96, 91), (91, 3), (3, 8), (8, 96), (96, 90), (90, 3), (3, 9), (9, 96), (95, 90), (90, 4), (4, 9), (9, 95), (94, 90), (90, 5), (5, 9), (9, 94), (93, 90), (90, 6), (6, 9), (9, 93), (93, 89), (89, 6), (6, 10), (10, 93), (93, 88), (88, 6), (6, 11), (11, 93), (93, 87), (87, 6), (6, 12), (12, 93), (94, 87), (87, 5), (5, 12), (12, 94), (95, 87), (87, 4), (4, 12), (12, 95), (96, 87), (87, 3), (3, 12), (12, 96), (96, 86), (86, 3), (3, 13), (13, 96), (96, 85), (85, 3), (3, 14), (14, 96), (96, 84), (84, 3), (3, 15), (15, 96), (96, 83), (83, 3), (3, 16), (16, 96), (96, 82), (82, 3), (3, 17), (17, 96), (96, 81), (81, 3), (3, 18), (18, 96), (95, 81), (81, 4), (4, 18), (18, 95), (94, 81), (81, 5), (5, 18), (18, 94), (93, 81), (81, 6), (6, 18), (18, 93), (93, 82), (82, 6), (6, 17), (17, 93), (93, 83), (83, 6), (6, 16), (16, 93), (93, 84), (84, 6), (6, 15), (15, 93), (92, 84), (84, 7), (7, 15), (15, 92), (91, 84), (84, 8), (8, 15), (15, 91), (90, 84), (84, 9), (9, 15), (15, 90), (89, 84), (84, 10), (10, 15), (15, 89), (88, 84), (84, 11), (11, 15), (15, 88), (87, 84), (84, 12), (12, 15), (15, 87), (87, 83), (83, 12), (12, 16), (16, 87), (87, 82), (82, 12), (12, 17), (17, 87), (87, 81), (81, 12), (12, 18), (18, 87), (88, 81), (81, 11), (11, 18), (18, 88), (89, 81), (81, 10), (10, 18), (18, 89), (90, 81), (81, 9), (9, 18), (18, 90), (90, 80), (80, 9), (9, 19), (19, 90), (90, 79), (79, 9), (9, 20), (20, 90), (90, 78), (78, 9), (9, 21), (21, 90), (89, 78), (78, 10), (10, 21), (21, 89), (88, 78), (78, 11), (11, 21), (21, 88), (87, 78), (78, 12), (12, 21), (21, 87), (87, 77), (77, 12), (12, 22), (22, 87), (87, 76), (76, 12), (12, 23), (23, 87), (87, 75), (75, 12), (12, 24), (24, 87), (88, 75), (75, 11), (11, 24), (24, 88), (89, 75), (75, 10), (10, 24), (24, 89), (90, 75), (75, 9), (9, 24), (24, 90), (91, 75), (75, 8), (8, 24), (24, 91), (92, 75), (75, 7), (7, 24), (24, 92), (93, 75), (75, 6), (6, 24), (24, 93), (93, 76), (76, 6), (6, 23), (23, 93), (93, 77), (77, 6), (6, 22), (22, 93), (93, 78), (78, 6), (6, 21), (21, 93), (94, 78), (78, 5), (5, 21), (21, 94), (95, 78), (78, 4), (4, 21), (21, 95), (96, 78), (78, 3), (3, 21), (21, 96), (96, 77), (77, 3), (3, 22), (22, 96), (96, 76), (76, 3), (3, 23), (23, 96), (96, 75), (75, 3), (3, 24), (24, 96), (96, 74), (74, 3), (3, 25), (25, 96), (96, 73), (73, 3), (3, 26), (26, 96), (96, 72), (72, 3), (3, 27), (27, 96), (95, 72), (72, 4), (4, 27), (27, 95), (94, 72), (72, 5), (5, 27), (27, 94), (93, 72), (72, 6), (6, 27), (27, 93), (93, 71), (71, 6), (6, 28), (28, 93), (93, 70), (70, 6), (6, 29), (29, 93), (93, 69), (69, 6), (6, 30), (30, 93), (94, 69), (69, 5), (5, 30), (30, 94), (95, 69), (69, 4), (4, 30), (30, 95), (96, 69), (69, 3), (3, 30), (30, 96), (96, 68), (68, 3), (3, 31), (31, 96), (96, 67), (67, 3), (3, 32), (32, 96), (96, 66), (66, 3), (3, 33), (33, 96), (96, 65), (65, 3), (3, 34), (34, 96), (96, 64), (64, 3), (3, 35), (35, 96), (96, 63), (63, 3), (3, 36), (36, 96), (95, 63), (63, 4), (4, 36), (36, 95), (94, 63), (63, 5), (5, 36), (36, 94), (93, 63), (63, 6), (6, 36), (36, 93), (93, 64), (64, 6), (6, 35), (35, 93), (93, 65), (65, 6), (6, 34), (34, 93), (93, 66), (66, 6), (6, 33), (33, 93), (92, 66), (66, 7), (7, 33), (33, 92), (91, 66), (66, 8), (8, 33), (33, 91), (90, 66), (66, 9), (9, 33), (33, 90), (90, 65), (65, 9), (9, 34), (34, 90), (90, 64), (64, 9), (9, 35), (35, 90), (90, 63), (63, 9), (9, 36), (36, 90), (89, 63), (63, 10), (10, 36), (36, 89), (88, 63), (63, 11), (11, 36), (36, 88), (87, 63), (63, 12), (12, 36), (36, 87), (87, 64), (64, 12), (12, 35), (35, 87), (87, 65), (65, 12), (12, 34), (34, 87), (87, 66), (66, 12), (12, 33), (33, 87), (87, 67), (67, 12), (12, 32), (32, 87), (87, 68), (68, 12), (12, 31), (31, 87), (87, 69), (69, 12), (12, 30), (30, 87), (88, 69), (69, 11), (11, 30), (30, 88), (89, 69), (69, 10), (10, 30), (30, 89), (90, 69), (69, 9), (9, 30), (30, 90), (90, 70), (70, 9), (9, 29), (29, 90), (90, 71), (71, 9), (9, 28), (28, 90), (90, 72), (72, 9), (9, 27), (27, 90), (89, 72), (72, 10), (10, 27), (27, 89), (88, 72), (72, 11), (11, 27), (27, 88), (87, 72), (72, 12), (12, 27), (27, 87), (86, 72), (72, 13), (13, 27), (27, 86), (85, 72), (72, 14), (14, 27), (27, 85), (84, 72), (72, 15), (15, 27), (27, 84), (84, 71), (71, 15), (15, 28), (28, 84), (84, 70), (70, 15), (15, 29), (29, 84), (84, 69), (69, 15), (15, 30), (30, 84), (83, 69), (69, 16), (16, 30), (30, 83), (82, 69), (69, 17), (17, 30), (30, 82), (81, 69), (69, 18), (18, 30), (30, 81), (81, 70), (70, 18), (18, 29), (29, 81), (81, 71), (71, 18), (18, 28), (28, 81), (81, 72), (72, 18), (18, 27), (27, 81), (80, 72), (72, 19), (19, 27), (27, 80), (79, 72), (72, 20), (20, 27), (27, 79), (78, 72), (72, 21), (21, 27), (27, 78), (77, 72), (72, 22), (22, 27), (27, 77), (76, 72), (72, 23), (23, 27), (27, 76), (75, 72), (72, 24), (24, 27), (27, 75), (75, 71), (71, 24), (24, 28), (28, 75), (75, 70), (70, 24), (24, 29), (29, 75), (75, 69), (69, 24), (24, 30), (30, 75), (76, 69), (69, 23), (23, 30), (30, 76), (77, 69), (69, 22), (22, 30), (30, 77), (78, 69), (69, 21), (21, 30), (30, 78), (78, 68), (68, 21), (21, 31), (31, 78), (78, 67), (67, 21), (21, 32), (32, 78), (78, 66), (66, 21), (21, 33), (33, 78), (77, 66), (66, 22), (22, 33), (33, 77), (76, 66), (66, 23), (23, 33), (33, 76), (75, 66), (66, 24), (24, 33), (33, 75), (75, 65), (65, 24), (24, 34), (34, 75), (75, 64), (64, 24), (24, 35), (35, 75), (75, 63), (63, 24), (24, 36), (36, 75), (76, 63), (63, 23), (23, 36), (36, 76), (77, 63), (63, 22), (22, 36), (36, 77), (78, 63), (63, 21), (21, 36), (36, 78), (79, 63), (63, 20), (20, 36), (36, 79), (80, 63), (63, 19), (19, 36), (36, 80), (81, 63), (63, 18), (18, 36), (36, 81), (81, 64), (64, 18), (18, 35), (35, 81), (81, 65), (65, 18), (18, 34), (34, 81), (81, 66), (66, 18), (18, 33), (33, 81), (82, 66), (66, 17), (17, 33), (33, 82), (83, 66), (66, 16), (16, 33), (33, 83), (84, 66), (66, 15), (15, 33), (33, 84), (84, 65), (65, 15), (15, 34), (34, 84), (84, 64), (64, 15), (15, 35), (35, 84), (84, 63), (63, 15), (15, 36), (36, 84), (84, 62), (62, 15), (15, 37), (37, 84), (84, 61), (61, 15), (15, 38), (38, 84), (84, 60), (60, 15), (15, 39), (39, 84), (84, 59), (59, 15), (15, 40), (40, 84), (84, 58), (58, 15), (15, 41), (41, 84), (84, 57), (57, 15), (15, 42), (42, 84), (83, 57), (57, 16), (16, 42), (42, 83), (82, 57), (57, 17), (17, 42), (42, 82), (81, 57), (57, 18), (18, 42), (42, 81), (81, 58), (58, 18), (18, 41), (41, 81), (81, 59), (59, 18), (18, 40), (40, 81), (81, 60), (60, 18), (18, 39), (39, 81), (80, 60), (60, 19), (19, 39), (39, 80), (79, 60), (60, 20), (20, 39), (39, 79), (78, 60), (60, 21), (21, 39), (39, 78), (77, 60), (60, 22), (22, 39), (39, 77), (76, 60), (60, 23), (23, 39), (39, 76), (75, 60), (60, 24), (24, 39), (39, 75), (75, 59), (59, 24), (24, 40), (40, 75), (75, 58), (58, 24), (24, 41), (41, 75), (75, 57), (57, 24), (24, 42), (42, 75), (76, 57), (57, 23), (23, 42), (42, 76), (77, 57), (57, 22), (22, 42), (42, 77), (78, 57), (57, 21), (21, 42), (42, 78), (78, 56), (56, 21), (21, 43), (43, 78), (78, 55), (55, 21), (21, 44), (44, 78), (78, 54), (54, 21), (21, 45), (45, 78), (77, 54), (54, 22), (22, 45), (45, 77), (76, 54), (54, 23), (23, 45), (45, 76), (75, 54), (54, 24), (24, 45), (45, 75), (75, 53), (53, 24), (24, 46), (46, 75), (75, 52), (52, 24), (24, 47), (47, 75), (75, 51), (51, 24), (24, 48), (48, 75), (76, 51), (51, 23), (23, 48), (48, 76), (77, 51), (51, 22), (22, 48), (48, 77), (78, 51), (51, 21), (21, 48), (48, 78), (79, 51), (51, 20), (20, 48), (48, 79), (80, 51), (51, 19), (19, 48), (48, 80), (81, 51), (51, 18), (18, 48), (48, 81), (81, 52), (52, 18), (18, 47), (47, 81), (81, 53), (53, 18), (18, 46), (46, 81), (81, 54), (54, 18), (18, 45), (45, 81), (82, 54), (54, 17), (17, 45), (45, 82), (83, 54), (54, 16), (16, 45), (45, 83), (84, 54), (54, 15), (15, 45), (45, 84), (84, 53), (53, 15), (15, 46), (46, 84), (84, 52), (52, 15), (15, 47), (47, 84), (84, 51), (51, 15), (15, 48), (48, 84), (85, 51), (51, 14), (14, 48), (48, 85), (86, 51), (51, 13), (13, 48), (48, 86), (87, 51), (51, 12), (12, 48), (48, 87), (88, 51), (51, 11), (11, 48), (48, 88), (89, 51), (51, 10), (10, 48), (48, 89), (90, 51), (51, 9), (9, 48), (48, 90), (90, 52), (52, 9), (9, 47), (47, 90), (90, 53), (53, 9), (9, 46), (46, 90), (90, 54), (54, 9), (9, 45), (45, 90), (89, 54), (54, 10), (10, 45), (45, 89), (88, 54), (54, 11), (11, 45), (45, 88), (87, 54), (54, 12), (12, 45), (45, 87), (87, 55), (55, 12), (12, 44), (44, 87), (87, 56), (56, 12), (12, 43), (43, 87), (87, 57), (57, 12), (12, 42), (42, 87), (87, 58), (58, 12), (12, 41), (41, 87), (87, 59), (59, 12), (12, 40), (40, 87), (87, 60), (60, 12), (12, 39), (39, 87), (88, 60), (60, 11), (11, 39), (39, 88), (89, 60), (60, 10), (10, 39), (39, 89), (90, 60), (60, 9), (9, 39), (39, 90), (90, 59), (59, 9), (9, 40), (40, 90), (90, 58), (58, 9), (9, 41), (41, 90), (90, 57), (57, 9), (9, 42), (42, 90), (91, 57), (57, 8), (8, 42), (42, 91), (92, 57), (57, 7), (7, 42), (42, 92), (93, 57), (57, 6), (6, 42), (42, 93), (93, 58), (58, 6), (6, 41), (41, 93), (93, 59), (59, 6), (6, 40), (40, 93), (93, 60), (60, 6), (6, 39), (39, 93), (94, 60), (60, 5), (5, 39), (39, 94), (95, 60), (60, 4), (4, 39), (39, 95), (96, 60), (60, 3), (3, 39), (39, 96), (96, 59), (59, 3), (3, 40), (40, 96), (96, 58), (58, 3), (3, 41), (41, 96), (96, 57), (57, 3), (3, 42), (42, 96), (96, 56), (56, 3), (3, 43), (43, 96), (96, 55), (55, 3), (3, 44), (44, 96), (96, 54), (54, 3), (3, 45), (45, 96), (95, 54), (54, 4), (4, 45), (45, 95), (94, 54), (54, 5), (5, 45), (45, 94), (93, 54), (54, 6), (6, 45), (45, 93), (93, 53), (53, 6), (6, 46), (46, 93), (93, 52), (52, 6), (6, 47), (47, 93), (93, 51), (51, 6), (6, 48), (48, 93), (94, 51), (51, 5), (5, 48), (48, 94), (95, 51), (51, 4), (4, 48), (48, 95), (96, 51), (51, 3), (3, 48), (48, 96)]

    def get_next_formation_points(self, state):
        return self.all_points
    
    def get_phase(self, phase, state, retract, movable):
        return 0

class QuadraticFormation(Formation):
    def __init__(self):
        self.all_points = [(50, 50), (49, 50), (49, 49), (48, 49), (48, 48), (47, 48), (47, 47), (46, 47), (46, 46), (45, 46), (45, 45), (44, 45), (44, 44), (43, 44), (43, 43), (42, 43), (42, 42), (41, 42), (41, 41), (40, 41), (40, 40), (39, 40), (39, 39), (38, 39), (38, 38), (37, 38), (37, 37), (36, 37), (36, 36), (35, 36), (35, 35), (34, 35), (34, 34), (33, 34), (33, 33), (32, 33), (32, 32), (31, 32), (31, 31), (30, 31), (30, 30), (29, 30), (29, 29), (28, 29), (28, 28), (27, 28), (27, 27), (26, 27), (26, 26), (25, 26), (25, 25), (24, 25), (24, 24), (23, 24), (23, 23), (22, 23), (22, 22), (21, 22), (21, 21), (20, 21), (20, 20), (19, 20), (19, 19), (18, 19), (18, 18), (17, 18), (17, 17), (16, 17), (16, 16), (15, 16), (15, 15), (14, 15), (14, 14), (13, 14), (13, 13), (12, 13), (12, 12), (11, 12), (11, 11), (10, 11), (10, 10), (9, 10), (9, 9), (8, 9), (8, 8), (7, 8), (7, 7), (6, 7), (6, 6), (5, 6), (5, 5), (4, 5), (4, 4), (3, 4), (3, 3), (2, 3), (2, 2), (1, 2), (1, 1), (0, 1), (0, 0), (51, 50), (51, 49), (52, 49), (52, 48), (53, 48), (53, 47), (54, 47), (54, 46), (55, 46), (55, 45), (56, 45), (56, 44), (57, 44), (57, 43), (58, 43), (58, 42), (59, 42), (59, 41), (60, 41), (60, 40), (61, 40), (61, 39), (62, 39), (62, 38), (63, 38), (63, 37), (64, 37), (64, 36), (65, 36), (65, 35), (66, 35), (66, 34), (67, 34), (67, 33), (68, 33), (68, 32), (69, 32), (69, 31), (70, 31), (70, 30), (71, 30), (71, 29), (72, 29), (72, 28), (73, 28), (73, 27), (74, 27), (74, 26), (75, 26), (75, 25), (76, 25), (76, 24), (77, 24), (77, 23), (78, 23), (78, 22), (79, 22), (79, 21), (80, 21), (80, 20), (81, 20), (81, 19), (82, 19), (82, 18), (83, 18), (83, 17), (84, 17), (84, 16), (85, 16), (85, 15), (86, 15), (86, 14), (87, 14), (87, 13), (88, 13), (88, 12), (89, 12), (89, 11), (90, 11), (90, 10), (91, 10), (91, 9), (92, 9), (92, 8), (93, 8), (93, 7), (94, 7), (94, 6), (95, 6), (95, 5), (96, 5), (96, 4), (97, 4), (97, 3), (98, 3), (98, 2), (99, 2), (99, 1), (99, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0), (11, 0), (12, 0), (13, 0), (14, 0), (15, 0), (16, 0), (17, 0), (18, 0), (19, 0), (20, 0), (21, 0), (22, 0), (23, 0), (24, 0), (25, 0), (26, 0), (27, 0), (28, 0), (29, 0), (30, 0), (31, 0), (32, 0), (33, 0), (34, 0), (35, 0), (36, 0), (37, 0), (38, 0), (39, 0), (40, 0), (41, 0), (42, 0), (43, 0), (44, 0), (45, 0), (46, 0), (47, 0), (48, 0), (49, 0), (50, 0), (51, 0), (52, 0), (53, 0), (54, 0), (55, 0), (56, 0), (57, 0), (58, 0), (59, 0), (60, 0), (61, 0), (62, 0), (63, 0), (64, 0), (65, 0), (66, 0), (67, 0), (68, 0), (69, 0), (70, 0), (71, 0), (72, 0), (73, 0), (74, 0), (75, 0), (76, 0), (77, 0), (78, 0), (79, 0), (80, 0), (81, 0), (82, 0), (83, 0), (84, 0), (85, 0), (86, 0), (87, 0), (88, 0), (89, 0), (90, 0), (91, 0), (92, 0), (93, 0), (94, 0), (95, 0), (96, 0), (97, 0), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1), (10, 1), (11, 1), (12, 1), (13, 1), (14, 1), (15, 1), (16, 1), (17, 1), (18, 1), (19, 1), (20, 1), (21, 1), (22, 1), (23, 1), (24, 1), (25, 1), (26, 1), (27, 1), (28, 1), (29, 1), (30, 1), (31, 1), (32, 1), (33, 1), (34, 1), (35, 1), (36, 1), (37, 1), (38, 1), (39, 1), (40, 1), (41, 1), (42, 1), (43, 1), (44, 1), (45, 1), (46, 1), (47, 1), (48, 1), (49, 1), (50, 1), (51, 1), (52, 1), (53, 1), (54, 1), (55, 1), (56, 1), (57, 1), (58, 1), (59, 1), (60, 1), (61, 1), (62, 1), (63, 1), (64, 1), (65, 1), (66, 1), (67, 1), (68, 1), (69, 1), (70, 1), (71, 1), (72, 1), (73, 1), (74, 1), (75, 1), (76, 1), (77, 1), (78, 1), (79, 1), (80, 1), (81, 1), (82, 1), (83, 1), (84, 1), (85, 1), (86, 1), (87, 1), (88, 1), (89, 1), (90, 1), (91, 1), (92, 1), (93, 1), (94, 1), (95, 1), (96, 1), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2), (11, 2), (12, 2), (13, 2), (14, 2), (15, 2), (16, 2), (17, 2), (18, 2), (19, 2), (20, 2), (21, 2), (22, 2), (23, 2), (24, 2), (25, 2), (26, 2), (27, 2), (28, 2), (29, 2), (30, 2), (31, 2), (32, 2), (33, 2), (34, 2), (35, 2), (36, 2), (37, 2), (38, 2), (39, 2), (40, 2), (41, 2), (42, 2), (43, 2), (44, 2), (45, 2), (46, 2), (47, 2), (48, 2), (49, 2), (50, 2), (51, 2), (52, 2), (53, 2), (54, 2), (55, 2), (56, 2), (57, 2), (58, 2), (59, 2), (60, 2), (61, 2), (62, 2), (63, 2), (64, 2), (65, 2), (66, 2), (67, 2), (68, 2), (69, 2), (70, 2), (71, 2), (72, 2), (73, 2), (74, 2), (75, 2), (76, 2), (77, 2), (78, 2), (79, 2), (80, 2), (81, 2), (82, 2), (83, 2), (84, 2), (85, 2), (86, 2), (87, 2), (88, 2), (89, 2), (90, 2), (91, 2), (92, 2), (93, 2), (94, 2), (95, 2), (5, 3), (6, 3), (7, 3), (8, 3), (9, 3), (10, 3), (11, 3), (12, 3), (13, 3), (14, 3), (15, 3), (16, 3), (17, 3), (18, 3), (19, 3), (20, 3), (21, 3), (22, 3), (23, 3), (24, 3), (25, 3), (26, 3), (27, 3), (28, 3), (29, 3), (30, 3), (31, 3), (32, 3), (33, 3), (34, 3), (35, 3), (36, 3), (37, 3), (38, 3), (39, 3), (40, 3), (41, 3), (42, 3), (43, 3), (44, 3), (45, 3), (46, 3), (47, 3), (48, 3), (49, 3), (50, 3), (51, 3), (52, 3), (53, 3), (54, 3), (55, 3), (56, 3), (57, 3), (58, 3), (59, 3), (60, 3), (61, 3), (62, 3), (63, 3), (64, 3), (65, 3), (66, 3), (67, 3), (68, 3), (69, 3), (70, 3), (71, 3), (72, 3), (73, 3), (74, 3), (75, 3), (76, 3), (77, 3), (78, 3), (79, 3), (80, 3), (81, 3), (82, 3), (83, 3), (84, 3), (85, 3), (86, 3), (87, 3), (88, 3), (89, 3), (90, 3), (91, 3), (92, 3), (93, 3), (94, 3), (6, 4), (7, 4), (8, 4), (9, 4), (10, 4), (11, 4), (12, 4), (13, 4), (14, 4), (15, 4), (16, 4), (17, 4), (18, 4), (19, 4), (20, 4), (21, 4), (22, 4), (23, 4), (24, 4), (25, 4), (26, 4), (27, 4), (28, 4), (29, 4), (30, 4), (31, 4), (32, 4), (33, 4), (34, 4), (35, 4), (36, 4), (37, 4), (38, 4), (39, 4), (40, 4), (41, 4), (42, 4), (43, 4), (44, 4), (45, 4), (46, 4), (47, 4), (48, 4), (49, 4), (50, 4), (51, 4), (52, 4), (53, 4), (54, 4), (55, 4), (56, 4), (57, 4), (58, 4), (59, 4), (60, 4), (61, 4), (62, 4), (63, 4), (64, 4), (65, 4), (66, 4), (67, 4), (68, 4), (69, 4), (70, 4), (71, 4), (72, 4), (73, 4), (74, 4), (75, 4), (76, 4), (77, 4), (78, 4), (79, 4), (80, 4), (81, 4), (82, 4), (83, 4), (84, 4), (85, 4), (86, 4), (87, 4), (88, 4), (89, 4), (90, 4), (91, 4), (92, 4), (93, 4), (7, 5), (8, 5), (9, 5), (10, 5), (11, 5), (12, 5), (13, 5), (14, 5), (15, 5), (16, 5), (17, 5), (18, 5), (19, 5), (20, 5), (21, 5), (22, 5), (23, 5), (24, 5), (25, 5), (26, 5), (27, 5), (28, 5), (29, 5), (30, 5), (31, 5), (32, 5), (33, 5), (34, 5), (35, 5), (36, 5), (37, 5), (38, 5), (39, 5), (40, 5), (41, 5), (42, 5), (43, 5), (44, 5), (45, 5), (46, 5), (47, 5), (48, 5), (49, 5), (50, 5), (51, 5), (52, 5), (53, 5), (54, 5), (55, 5), (56, 5), (57, 5), (58, 5), (59, 5), (60, 5), (61, 5), (62, 5), (63, 5), (64, 5), (65, 5), (66, 5), (67, 5), (68, 5), (69, 5), (70, 5), (71, 5), (72, 5), (73, 5), (74, 5), (75, 5), (76, 5), (77, 5), (78, 5), (79, 5), (80, 5), (81, 5), (82, 5), (83, 5), (84, 5), (85, 5), (86, 5), (87, 5), (88, 5), (89, 5), (90, 5), (91, 5), (92, 5), (8, 6), (9, 6), (10, 6), (11, 6), (12, 6), (13, 6), (14, 6), (15, 6), (16, 6), (17, 6), (18, 6), (19, 6), (20, 6), (21, 6), (22, 6), (23, 6), (24, 6), (25, 6), (26, 6), (27, 6), (28, 6), (29, 6), (30, 6), (31, 6), (32, 6), (33, 6), (34, 6), (35, 6), (36, 6), (37, 6), (38, 6), (39, 6), (40, 6), (41, 6), (42, 6), (43, 6), (44, 6), (45, 6), (46, 6), (47, 6), (48, 6), (49, 6), (50, 6), (51, 6), (52, 6), (53, 6), (54, 6), (55, 6), (56, 6), (57, 6), (58, 6), (59, 6), (60, 6), (61, 6), (62, 6), (63, 6), (64, 6), (65, 6), (66, 6), (67, 6), (68, 6), (69, 6), (70, 6), (71, 6), (72, 6), (73, 6), (74, 6), (75, 6), (76, 6), (77, 6), (78, 6), (79, 6), (80, 6), (81, 6), (82, 6), (83, 6), (84, 6), (85, 6), (86, 6), (87, 6), (88, 6), (89, 6), (90, 6), (91, 6), (9, 7), (10, 7), (11, 7), (12, 7), (13, 7), (14, 7), (15, 7), (16, 7), (17, 7), (18, 7), (19, 7), (20, 7), (21, 7), (22, 7), (23, 7), (24, 7), (25, 7), (26, 7), (27, 7), (28, 7), (29, 7), (30, 7), (31, 7), (32, 7), (33, 7), (34, 7), (35, 7), (36, 7), (37, 7), (38, 7), (39, 7), (40, 7), (41, 7), (42, 7), (43, 7), (44, 7), (45, 7), (46, 7), (47, 7), (48, 7), (49, 7), (50, 7), (51, 7), (52, 7), (53, 7), (54, 7), (55, 7), (56, 7), (57, 7), (58, 7), (59, 7), (60, 7), (61, 7), (62, 7), (63, 7), (64, 7), (65, 7), (66, 7), (67, 7), (68, 7), (69, 7), (70, 7), (71, 7), (72, 7), (73, 7), (74, 7), (75, 7), (76, 7), (77, 7), (78, 7), (79, 7), (80, 7), (81, 7), (82, 7), (83, 7), (84, 7), (85, 7), (86, 7), (87, 7), (88, 7), (89, 7), (90, 7), (10, 8), (11, 8), (12, 8), (13, 8), (14, 8), (15, 8), (16, 8), (17, 8), (18, 8), (19, 8), (20, 8), (21, 8), (22, 8), (23, 8), (24, 8), (25, 8), (26, 8), (27, 8), (28, 8), (29, 8), (30, 8), (31, 8), (32, 8), (33, 8), (34, 8), (35, 8), (36, 8), (37, 8), (38, 8), (39, 8), (40, 8), (41, 8), (42, 8), (43, 8), (44, 8), (45, 8), (46, 8), (47, 8), (48, 8), (49, 8), (50, 8), (51, 8), (52, 8), (53, 8), (54, 8), (55, 8), (56, 8), (57, 8), (58, 8), (59, 8), (60, 8), (61, 8), (62, 8), (63, 8), (64, 8), (65, 8), (66, 8), (67, 8), (68, 8), (69, 8), (70, 8), (71, 8), (72, 8), (73, 8), (74, 8), (75, 8), (76, 8), (77, 8), (78, 8), (79, 8), (80, 8), (81, 8), (82, 8), (83, 8), (84, 8), (85, 8), (86, 8), (87, 8), (88, 8), (89, 8), (11, 9), (12, 9), (13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (19, 9), (20, 9), (21, 9), (22, 9), (23, 9), (24, 9), (25, 9), (26, 9), (27, 9), (28, 9), (29, 9), (30, 9), (31, 9), (32, 9), (33, 9), (34, 9), (35, 9), (36, 9), (37, 9), (38, 9), (39, 9), (40, 9), (41, 9), (42, 9), (43, 9), (44, 9), (45, 9), (46, 9), (47, 9), (48, 9), (49, 9), (50, 9), (51, 9), (52, 9), (53, 9), (54, 9), (55, 9), (56, 9), (57, 9), (58, 9), (59, 9), (60, 9), (61, 9), (62, 9), (63, 9), (64, 9), (65, 9), (66, 9), (67, 9), (68, 9), (69, 9), (70, 9), (71, 9), (72, 9), (73, 9), (74, 9), (75, 9), (76, 9), (77, 9), (78, 9), (79, 9), (80, 9), (81, 9), (82, 9), (83, 9), (84, 9), (85, 9), (86, 9), (87, 9), (88, 9), (12, 10), (13, 10), (14, 10), (15, 10), (16, 10), (17, 10), (18, 10), (19, 10), (20, 10), (21, 10), (22, 10), (23, 10), (24, 10), (25, 10), (26, 10), (27, 10), (28, 10), (29, 10), (30, 10), (31, 10), (32, 10), (33, 10), (34, 10), (35, 10), (36, 10), (37, 10), (38, 10), (39, 10), (40, 10), (41, 10), (42, 10), (43, 10), (44, 10), (45, 10), (46, 10), (47, 10), (48, 10), (49, 10), (50, 10), (51, 10), (52, 10), (53, 10), (54, 10), (55, 10), (56, 10), (57, 10), (58, 10), (59, 10), (60, 10), (61, 10), (62, 10), (63, 10), (64, 10), (65, 10), (66, 10), (67, 10), (68, 10), (69, 10), (70, 10), (71, 10), (72, 10), (73, 10), (74, 10), (75, 10), (76, 10), (77, 10), (78, 10), (79, 10), (80, 10), (81, 10), (82, 10), (83, 10), (84, 10), (85, 10), (86, 10), (87, 10), (13, 11), (14, 11), (15, 11), (16, 11), (17, 11), (18, 11), (19, 11), (20, 11), (21, 11), (22, 11), (23, 11), (24, 11), (25, 11), (26, 11), (27, 11), (28, 11), (29, 11), (30, 11), (31, 11), (32, 11), (33, 11), (34, 11), (35, 11), (36, 11), (37, 11), (38, 11), (39, 11), (40, 11), (41, 11), (42, 11), (43, 11), (44, 11), (45, 11), (46, 11), (47, 11), (48, 11), (49, 11), (50, 11), (51, 11), (52, 11), (53, 11), (54, 11), (55, 11), (56, 11), (57, 11), (58, 11), (59, 11), (60, 11), (61, 11), (62, 11), (63, 11), (64, 11), (65, 11), (66, 11), (67, 11), (68, 11), (69, 11), (70, 11), (71, 11), (72, 11), (73, 11), (74, 11), (75, 11), (76, 11), (77, 11), (78, 11), (79, 11), (80, 11), (81, 11), (82, 11), (83, 11), (84, 11), (85, 11), (86, 11), (14, 12), (15, 12), (16, 12), (17, 12), (18, 12), (19, 12), (20, 12), (21, 12), (22, 12), (23, 12), (24, 12), (25, 12), (26, 12), (27, 12), (28, 12), (29, 12), (30, 12), (31, 12), (32, 12), (33, 12), (34, 12), (35, 12), (36, 12), (37, 12), (38, 12), (39, 12), (40, 12), (41, 12), (42, 12), (43, 12), (44, 12), (45, 12), (46, 12), (47, 12), (48, 12), (49, 12), (50, 12), (51, 12), (52, 12), (53, 12), (54, 12), (55, 12), (56, 12), (57, 12), (58, 12), (59, 12), (60, 12), (61, 12), (62, 12), (63, 12), (64, 12), (65, 12), (66, 12), (67, 12), (68, 12), (69, 12), (70, 12), (71, 12), (72, 12), (73, 12), (74, 12), (75, 12), (76, 12), (77, 12), (78, 12), (79, 12), (80, 12), (81, 12), (82, 12), (83, 12), (84, 12), (85, 12), (15, 13), (16, 13), (17, 13), (18, 13), (19, 13), (20, 13), (21, 13), (22, 13), (23, 13), (24, 13), (25, 13), (26, 13), (27, 13), (28, 13), (29, 13), (30, 13), (31, 13), (32, 13), (33, 13), (34, 13), (35, 13), (36, 13), (37, 13), (38, 13), (39, 13), (40, 13), (41, 13), (42, 13), (43, 13), (44, 13), (45, 13), (46, 13), (47, 13), (48, 13), (49, 13), (50, 13), (51, 13), (52, 13), (53, 13), (54, 13), (55, 13), (56, 13), (57, 13), (58, 13), (59, 13), (60, 13), (61, 13), (62, 13), (63, 13), (64, 13), (65, 13), (66, 13), (67, 13), (68, 13), (69, 13), (70, 13), (71, 13), (72, 13), (73, 13), (74, 13), (75, 13), (76, 13), (77, 13), (78, 13), (79, 13), (80, 13), (81, 13), (82, 13), (83, 13), (84, 13), (16, 14), (17, 14), (18, 14), (19, 14), (20, 14), (21, 14), (22, 14), (23, 14), (24, 14), (25, 14), (26, 14), (27, 14), (28, 14), (29, 14), (30, 14), (31, 14), (32, 14), (33, 14), (34, 14), (35, 14), (36, 14), (37, 14), (38, 14), (39, 14), (40, 14), (41, 14), (42, 14), (43, 14), (44, 14), (45, 14), (46, 14), (47, 14), (48, 14), (49, 14), (50, 14), (51, 14), (52, 14), (53, 14), (54, 14), (55, 14), (56, 14), (57, 14), (58, 14), (59, 14), (60, 14), (61, 14), (62, 14), (63, 14), (64, 14), (65, 14), (66, 14), (67, 14), (68, 14), (69, 14), (70, 14), (71, 14), (72, 14), (73, 14), (74, 14), (75, 14), (76, 14), (77, 14), (78, 14), (79, 14), (80, 14), (81, 14), (82, 14), (83, 14), (17, 15), (18, 15), (19, 15), (20, 15), (21, 15), (22, 15), (23, 15), (24, 15), (25, 15), (26, 15), (27, 15), (28, 15), (29, 15), (30, 15), (31, 15), (32, 15), (33, 15), (34, 15), (35, 15), (36, 15), (37, 15), (38, 15), (39, 15), (40, 15), (41, 15), (42, 15), (43, 15), (44, 15), (45, 15), (46, 15), (47, 15), (48, 15), (49, 15), (50, 15), (51, 15), (52, 15), (53, 15), (54, 15), (55, 15), (56, 15), (57, 15), (58, 15), (59, 15), (60, 15), (61, 15), (62, 15), (63, 15), (64, 15), (65, 15), (66, 15), (67, 15), (68, 15), (69, 15), (70, 15), (71, 15), (72, 15), (73, 15), (74, 15), (75, 15), (76, 15), (77, 15), (78, 15), (79, 15), (80, 15), (81, 15), (82, 15), (18, 16), (19, 16), (20, 16), (21, 16), (22, 16), (23, 16), (24, 16), (25, 16), (26, 16), (27, 16), (28, 16), (29, 16), (30, 16), (31, 16), (32, 16), (33, 16), (34, 16), (35, 16), (36, 16), (37, 16), (38, 16), (39, 16), (40, 16), (41, 16), (42, 16), (43, 16), (44, 16), (45, 16), (46, 16), (47, 16), (48, 16), (49, 16), (50, 16), (51, 16), (52, 16), (53, 16), (54, 16), (55, 16), (56, 16), (57, 16), (58, 16), (59, 16), (60, 16), (61, 16), (62, 16), (63, 16), (64, 16), (65, 16), (66, 16), (67, 16), (68, 16), (69, 16), (70, 16), (71, 16), (72, 16), (73, 16), (74, 16), (75, 16), (76, 16), (77, 16), (78, 16), (79, 16), (80, 16), (81, 16), (19, 17), (20, 17), (21, 17), (22, 17), (23, 17), (24, 17), (25, 17), (26, 17), (27, 17), (28, 17), (29, 17), (30, 17), (31, 17), (32, 17), (33, 17), (34, 17), (35, 17), (36, 17), (37, 17), (38, 17), (39, 17), (40, 17), (41, 17), (42, 17), (43, 17), (44, 17), (45, 17), (46, 17), (47, 17), (48, 17), (49, 17), (50, 17), (51, 17), (52, 17), (53, 17), (54, 17), (55, 17), (56, 17), (57, 17), (58, 17), (59, 17), (60, 17), (61, 17), (62, 17), (63, 17), (64, 17), (65, 17), (66, 17), (67, 17), (68, 17), (69, 17), (70, 17), (71, 17), (72, 17), (73, 17), (74, 17), (75, 17), (76, 17), (77, 17), (78, 17), (79, 17), (80, 17), (20, 18), (21, 18), (22, 18), (23, 18), (24, 18), (25, 18), (26, 18), (27, 18), (28, 18), (29, 18), (30, 18), (31, 18), (32, 18), (33, 18), (34, 18), (35, 18), (36, 18), (37, 18), (38, 18), (39, 18), (40, 18), (41, 18), (42, 18), (43, 18), (44, 18), (45, 18), (46, 18), (47, 18), (48, 18), (49, 18), (50, 18), (51, 18), (52, 18), (53, 18), (54, 18), (55, 18), (56, 18), (57, 18), (58, 18), (59, 18), (60, 18), (61, 18), (62, 18), (63, 18), (64, 18), (65, 18), (66, 18), (67, 18), (68, 18), (69, 18), (70, 18), (71, 18), (72, 18), (73, 18), (74, 18), (75, 18), (76, 18), (77, 18), (78, 18), (79, 18), (21, 19), (22, 19), (23, 19), (24, 19), (25, 19), (26, 19), (27, 19), (28, 19), (29, 19), (30, 19), (31, 19), (32, 19), (33, 19), (34, 19), (35, 19), (36, 19), (37, 19), (38, 19), (39, 19), (40, 19), (41, 19), (42, 19), (43, 19), (44, 19), (45, 19), (46, 19), (47, 19), (48, 19), (49, 19), (50, 19), (51, 19), (52, 19), (53, 19), (54, 19), (55, 19), (56, 19), (57, 19), (58, 19), (59, 19), (60, 19), (61, 19), (62, 19), (63, 19), (64, 19), (65, 19), (66, 19), (67, 19), (68, 19), (69, 19), (70, 19), (71, 19), (72, 19), (73, 19), (74, 19), (75, 19), (76, 19), (77, 19), (78, 19), (22, 20), (23, 20), (24, 20), (25, 20), (26, 20), (27, 20), (28, 20), (29, 20), (30, 20), (31, 20), (32, 20), (33, 20), (34, 20), (35, 20), (36, 20), (37, 20), (38, 20), (39, 20), (40, 20), (41, 20), (42, 20), (43, 20), (44, 20), (45, 20), (46, 20), (47, 20), (48, 20), (49, 20), (50, 20), (51, 20), (52, 20), (53, 20), (54, 20), (55, 20), (56, 20), (57, 20), (58, 20), (59, 20), (60, 20), (61, 20), (62, 20), (63, 20), (64, 20), (65, 20), (66, 20), (67, 20), (68, 20), (69, 20), (70, 20), (71, 20), (72, 20), (73, 20), (74, 20), (75, 20), (76, 20), (77, 20), (23, 21), (24, 21), (25, 21), (26, 21), (27, 21), (28, 21), (29, 21), (30, 21), (31, 21), (32, 21), (33, 21), (34, 21), (35, 21), (36, 21), (37, 21), (38, 21), (39, 21), (40, 21), (41, 21), (42, 21), (43, 21), (44, 21), (45, 21), (46, 21), (47, 21), (48, 21), (49, 21), (50, 21), (51, 21), (52, 21), (53, 21), (54, 21), (55, 21), (56, 21), (57, 21), (58, 21), (59, 21), (60, 21), (61, 21), (62, 21), (63, 21), (64, 21), (65, 21), (66, 21), (67, 21), (68, 21), (69, 21), (70, 21), (71, 21), (72, 21), (73, 21), (74, 21), (75, 21), (76, 21), (24, 22), (25, 22), (26, 22), (27, 22), (28, 22), (29, 22), (30, 22), (31, 22), (32, 22), (33, 22), (34, 22), (35, 22), (36, 22), (37, 22), (38, 22), (39, 22), (40, 22), (41, 22), (42, 22), (43, 22), (44, 22), (45, 22), (46, 22), (47, 22), (48, 22), (49, 22), (50, 22), (51, 22), (52, 22), (53, 22), (54, 22), (55, 22), (56, 22), (57, 22), (58, 22), (59, 22), (60, 22), (61, 22), (62, 22), (63, 22), (64, 22), (65, 22), (66, 22), (67, 22), (68, 22), (69, 22), (70, 22), (71, 22), (72, 22), (73, 22), (74, 22), (75, 22), (25, 23), (26, 23), (27, 23), (28, 23), (29, 23), (30, 23), (31, 23), (32, 23), (33, 23), (34, 23), (35, 23), (36, 23), (37, 23), (38, 23), (39, 23), (40, 23), (41, 23), (42, 23), (43, 23), (44, 23), (45, 23), (46, 23), (47, 23), (48, 23), (49, 23), (50, 23), (51, 23), (52, 23), (53, 23), (54, 23), (55, 23), (56, 23), (57, 23), (58, 23), (59, 23), (60, 23), (61, 23), (62, 23), (63, 23), (64, 23), (65, 23), (66, 23), (67, 23), (68, 23), (69, 23), (70, 23), (71, 23), (72, 23), (73, 23), (74, 23), (26, 24), (27, 24), (28, 24), (29, 24), (30, 24), (31, 24), (32, 24), (33, 24), (34, 24), (35, 24), (36, 24), (37, 24), (38, 24), (39, 24), (40, 24), (41, 24), (42, 24), (43, 24), (44, 24), (45, 24), (46, 24), (47, 24), (48, 24), (49, 24), (50, 24), (51, 24), (52, 24), (53, 24), (54, 24), (55, 24), (56, 24), (57, 24), (58, 24), (59, 24), (60, 24), (61, 24), (62, 24), (63, 24), (64, 24), (65, 24), (66, 24), (67, 24), (68, 24), (69, 24), (70, 24), (71, 24), (72, 24), (73, 24), (27, 25), (28, 25), (29, 25), (30, 25), (31, 25), (32, 25), (33, 25), (34, 25), (35, 25), (36, 25), (37, 25), (38, 25), (39, 25), (40, 25), (41, 25), (42, 25), (43, 25), (44, 25), (45, 25), (46, 25), (47, 25), (48, 25), (49, 25), (50, 25), (51, 25), (52, 25), (53, 25), (54, 25), (55, 25), (56, 25), (57, 25), (58, 25), (59, 25), (60, 25), (61, 25), (62, 25), (63, 25), (64, 25), (65, 25), (66, 25), (67, 25), (68, 25), (69, 25), (70, 25), (71, 25), (72, 25), (28, 26), (29, 26), (30, 26), (31, 26), (32, 26), (33, 26), (34, 26), (35, 26), (36, 26), (37, 26), (38, 26), (39, 26), (40, 26), (41, 26), (42, 26), (43, 26), (44, 26), (45, 26), (46, 26), (47, 26), (48, 26), (49, 26), (50, 26), (51, 26), (52, 26), (53, 26), (54, 26), (55, 26), (56, 26), (57, 26), (58, 26), (59, 26), (60, 26), (61, 26), (62, 26), (63, 26), (64, 26), (65, 26), (66, 26), (67, 26), (68, 26), (69, 26), (70, 26), (71, 26), (29, 27), (30, 27), (31, 27), (32, 27), (33, 27), (34, 27), (35, 27), (36, 27), (37, 27), (38, 27), (39, 27), (40, 27), (41, 27), (42, 27), (43, 27), (44, 27), (45, 27), (46, 27), (47, 27), (48, 27), (49, 27), (50, 27), (51, 27), (52, 27), (53, 27), (54, 27), (55, 27), (56, 27), (57, 27), (58, 27), (59, 27), (60, 27), (61, 27), (62, 27), (63, 27), (64, 27), (65, 27), (66, 27), (67, 27), (68, 27), (69, 27), (70, 27), (30, 28), (31, 28), (32, 28), (33, 28), (34, 28), (35, 28), (36, 28), (37, 28), (38, 28), (39, 28), (40, 28), (41, 28), (42, 28), (43, 28), (44, 28), (45, 28), (46, 28), (47, 28), (48, 28), (49, 28), (50, 28), (51, 28), (52, 28), (53, 28), (54, 28), (55, 28), (56, 28), (57, 28), (58, 28), (59, 28), (60, 28), (61, 28), (62, 28), (63, 28), (64, 28), (65, 28), (66, 28), (67, 28), (68, 28), (69, 28), (31, 29), (32, 29), (33, 29), (34, 29), (35, 29), (36, 29), (37, 29), (38, 29), (39, 29), (40, 29), (41, 29), (42, 29), (43, 29), (44, 29), (45, 29), (46, 29), (47, 29), (48, 29), (49, 29), (50, 29), (51, 29), (52, 29), (53, 29), (54, 29), (55, 29), (56, 29), (57, 29), (58, 29), (59, 29), (60, 29), (61, 29), (62, 29), (63, 29), (64, 29), (65, 29), (66, 29), (67, 29), (68, 29), (32, 30), (33, 30), (34, 30), (35, 30), (36, 30), (37, 30), (38, 30), (39, 30), (40, 30), (41, 30), (42, 30), (43, 30), (44, 30), (45, 30), (46, 30), (47, 30), (48, 30), (49, 30), (50, 30), (51, 30), (52, 30), (53, 30), (54, 30), (55, 30), (56, 30), (57, 30), (58, 30), (59, 30), (60, 30), (61, 30), (62, 30), (63, 30), (64, 30), (65, 30), (66, 30), (67, 30), (33, 31), (34, 31), (35, 31), (36, 31), (37, 31), (38, 31), (39, 31), (40, 31), (41, 31), (42, 31), (43, 31), (44, 31), (45, 31), (46, 31), (47, 31), (48, 31), (49, 31), (50, 31), (51, 31), (52, 31), (53, 31), (54, 31), (55, 31), (56, 31), (57, 31), (58, 31), (59, 31), (60, 31), (61, 31), (62, 31), (63, 31), (64, 31), (65, 31), (66, 31), (34, 32), (35, 32), (36, 32), (37, 32), (38, 32), (39, 32), (40, 32), (41, 32), (42, 32), (43, 32), (44, 32), (45, 32), (46, 32), (47, 32), (48, 32), (49, 32), (50, 32), (51, 32), (52, 32), (53, 32), (54, 32), (55, 32), (56, 32), (57, 32), (58, 32), (59, 32), (60, 32), (61, 32), (62, 32), (63, 32), (64, 32), (65, 32), (35, 33), (36, 33), (37, 33), (38, 33), (39, 33), (40, 33), (41, 33), (42, 33), (43, 33), (44, 33), (45, 33), (46, 33), (47, 33), (48, 33), (49, 33), (50, 33), (51, 33), (52, 33), (53, 33), (54, 33), (55, 33), (56, 33), (57, 33), (58, 33), (59, 33), (60, 33), (61, 33), (62, 33), (63, 33), (64, 33), (36, 34), (37, 34), (38, 34), (39, 34), (40, 34), (41, 34), (42, 34), (43, 34), (44, 34), (45, 34), (46, 34), (47, 34), (48, 34), (49, 34), (50, 34), (51, 34), (52, 34), (53, 34), (54, 34), (55, 34), (56, 34), (57, 34), (58, 34), (59, 34), (60, 34), (61, 34), (62, 34), (63, 34), (37, 35), (38, 35), (39, 35), (40, 35), (41, 35), (42, 35), (43, 35), (44, 35), (45, 35), (46, 35), (47, 35), (48, 35), (49, 35), (50, 35), (51, 35), (52, 35), (53, 35), (54, 35), (55, 35), (56, 35), (57, 35), (58, 35), (59, 35), (60, 35), (61, 35), (62, 35), (38, 36), (39, 36), (40, 36), (41, 36), (42, 36), (43, 36), (44, 36), (45, 36), (46, 36), (47, 36), (48, 36), (49, 36), (50, 36), (51, 36), (52, 36), (53, 36), (54, 36), (55, 36), (56, 36), (57, 36), (58, 36), (59, 36), (60, 36), (61, 36), (39, 37), (40, 37), (41, 37), (42, 37), (43, 37), (44, 37), (45, 37), (46, 37), (47, 37), (48, 37), (49, 37), (50, 37), (51, 37), (52, 37), (53, 37), (54, 37), (55, 37), (56, 37), (57, 37), (58, 37), (59, 37), (60, 37), (40, 38), (41, 38), (42, 38), (43, 38), (44, 38), (45, 38), (46, 38), (47, 38), (48, 38), (49, 38), (50, 38), (51, 38), (52, 38), (53, 38), (54, 38), (55, 38), (56, 38), (57, 38), (58, 38), (59, 38), (41, 39), (42, 39), (43, 39), (44, 39), (45, 39), (46, 39), (47, 39), (48, 39), (49, 39), (50, 39), (51, 39), (52, 39), (53, 39), (54, 39), (55, 39), (56, 39), (57, 39), (58, 39), (42, 40), (43, 40), (44, 40), (45, 40), (46, 40), (47, 40), (48, 40), (49, 40), (50, 40), (51, 40), (52, 40), (53, 40), (54, 40), (55, 40), (56, 40), (57, 40), (43, 41), (44, 41), (45, 41), (46, 41), (47, 41), (48, 41), (49, 41), (50, 41), (51, 41), (52, 41), (53, 41), (54, 41), (55, 41), (56, 41), (44, 42), (45, 42), (46, 42), (47, 42), (48, 42), (49, 42), (50, 42), (51, 42), (52, 42), (53, 42), (54, 42), (55, 42), (45, 43), (46, 43), (47, 43), (48, 43), (49, 43), (50, 43), (51, 43), (52, 43), (53, 43), (54, 43), (46, 44), (47, 44), (48, 44), (49, 44), (50, 44), (51, 44), (52, 44), (53, 44), (47, 45), (48, 45), (49, 45), (50, 45), (51, 45), (52, 45), (48, 46), (49, 46), (50, 46), (51, 46), (49, 47), (50, 47), (49, 51), (48, 51), (48, 52), (47, 52), (47, 53), (46, 53), (46, 54), (45, 54), (45, 55), (44, 55), (44, 56), (43, 56), (43, 57), (42, 57), (42, 58), (41, 58), (41, 59), (40, 59), (40, 60), (39, 60), (39, 61), (38, 61), (38, 62), (37, 62), (37, 63), (36, 63), (36, 64), (35, 64), (35, 65), (34, 65), (34, 66), (33, 66), (33, 67), (32, 67), (32, 68), (31, 68), (31, 69), (30, 69), (30, 70), (29, 70), (29, 71), (28, 71), (28, 72), (27, 72), (27, 73), (26, 73), (26, 74), (25, 74), (25, 75), (24, 75), (24, 76), (23, 76), (23, 77), (22, 77), (22, 78), (21, 78), (21, 79), (20, 79), (20, 80), (19, 80), (19, 81), (18, 81), (18, 82), (17, 82), (17, 83), (16, 83), (16, 84), (15, 84), (15, 85), (14, 85), (14, 86), (13, 86), (13, 87), (12, 87), (12, 88), (11, 88), (11, 89), (10, 89), (10, 90), (9, 90), (9, 91), (8, 91), (8, 92), (7, 92), (7, 93), (6, 93), (6, 94), (5, 94), (5, 95), (4, 95), (4, 96), (3, 96), (3, 97), (2, 97), (2, 98), (1, 98), (1, 99), (0, 99), (51, 51), (52, 51), (52, 52), (53, 52), (53, 53), (54, 53), (54, 54), (55, 54), (55, 55), (56, 55), (56, 56), (57, 56), (57, 57), (58, 57), (58, 58), (59, 58), (59, 59), (60, 59), (60, 60), (61, 60), (61, 61), (62, 61), (62, 62), (63, 62), (63, 63), (64, 63), (64, 64), (65, 64), (65, 65), (66, 65), (66, 66), (67, 66), (67, 67), (68, 67), (68, 68), (69, 68), (69, 69), (70, 69), (70, 70), (71, 70), (71, 71), (72, 71), (72, 72), (73, 72), (73, 73), (74, 73), (74, 74), (75, 74), (75, 75), (76, 75), (76, 76), (77, 76), (77, 77), (78, 77), (78, 78), (79, 78), (79, 79), (80, 79), (80, 80), (81, 80), (81, 81), (82, 81), (82, 82), (83, 82), (83, 83), (84, 83), (84, 84), (85, 84), (85, 85), (86, 85), (86, 86), (87, 86), (87, 87), (88, 87), (88, 88), (89, 88), (89, 89), (90, 89), (90, 90), (91, 90), (91, 91), (92, 91), (92, 92), (93, 92), (93, 93), (94, 93), (94, 94), (95, 94), (95, 95), (96, 95), (96, 96), (97, 96), (97, 97), (98, 97), (98, 98), (99, 98), (99, 99), (2, 99), (3, 99), (4, 99), (5, 99), (6, 99), (7, 99), (8, 99), (9, 99), (10, 99), (11, 99), (12, 99), (13, 99), (14, 99), (15, 99), (16, 99), (17, 99), (18, 99), (19, 99), (20, 99), (21, 99), (22, 99), (23, 99), (24, 99), (25, 99), (26, 99), (27, 99), (28, 99), (29, 99), (30, 99), (31, 99), (32, 99), (33, 99), (34, 99), (35, 99), (36, 99), (37, 99), (38, 99), (39, 99), (40, 99), (41, 99), (42, 99), (43, 99), (44, 99), (45, 99), (46, 99), (47, 99), (48, 99), (49, 99), (50, 99), (51, 99), (52, 99), (53, 99), (54, 99), (55, 99), (56, 99), (57, 99), (58, 99), (59, 99), (60, 99), (61, 99), (62, 99), (63, 99), (64, 99), (65, 99), (66, 99), (67, 99), (68, 99), (69, 99), (70, 99), (71, 99), (72, 99), (73, 99), (74, 99), (75, 99), (76, 99), (77, 99), (78, 99), (79, 99), (80, 99), (81, 99), (82, 99), (83, 99), (84, 99), (85, 99), (86, 99), (87, 99), (88, 99), (89, 99), (90, 99), (91, 99), (92, 99), (93, 99), (94, 99), (95, 99), (96, 99), (97, 99), (98, 99), (3, 98), (4, 98), (5, 98), (6, 98), (7, 98), (8, 98), (9, 98), (10, 98), (11, 98), (12, 98), (13, 98), (14, 98), (15, 98), (16, 98), (17, 98), (18, 98), (19, 98), (20, 98), (21, 98), (22, 98), (23, 98), (24, 98), (25, 98), (26, 98), (27, 98), (28, 98), (29, 98), (30, 98), (31, 98), (32, 98), (33, 98), (34, 98), (35, 98), (36, 98), (37, 98), (38, 98), (39, 98), (40, 98), (41, 98), (42, 98), (43, 98), (44, 98), (45, 98), (46, 98), (47, 98), (48, 98), (49, 98), (50, 98), (51, 98), (52, 98), (53, 98), (54, 98), (55, 98), (56, 98), (57, 98), (58, 98), (59, 98), (60, 98), (61, 98), (62, 98), (63, 98), (64, 98), (65, 98), (66, 98), (67, 98), (68, 98), (69, 98), (70, 98), (71, 98), (72, 98), (73, 98), (74, 98), (75, 98), (76, 98), (77, 98), (78, 98), (79, 98), (80, 98), (81, 98), (82, 98), (83, 98), (84, 98), (85, 98), (86, 98), (87, 98), (88, 98), (89, 98), (90, 98), (91, 98), (92, 98), (93, 98), (94, 98), (95, 98), (96, 98), (97, 98), (4, 97), (5, 97), (6, 97), (7, 97), (8, 97), (9, 97), (10, 97), (11, 97), (12, 97), (13, 97), (14, 97), (15, 97), (16, 97), (17, 97), (18, 97), (19, 97), (20, 97), (21, 97), (22, 97), (23, 97), (24, 97), (25, 97), (26, 97), (27, 97), (28, 97), (29, 97), (30, 97), (31, 97), (32, 97), (33, 97), (34, 97), (35, 97), (36, 97), (37, 97), (38, 97), (39, 97), (40, 97), (41, 97), (42, 97), (43, 97), (44, 97), (45, 97), (46, 97), (47, 97), (48, 97), (49, 97), (50, 97), (51, 97), (52, 97), (53, 97), (54, 97), (55, 97), (56, 97), (57, 97), (58, 97), (59, 97), (60, 97), (61, 97), (62, 97), (63, 97), (64, 97), (65, 97), (66, 97), (67, 97), (68, 97), (69, 97), (70, 97), (71, 97), (72, 97), (73, 97), (74, 97), (75, 97), (76, 97), (77, 97), (78, 97), (79, 97), (80, 97), (81, 97), (82, 97), (83, 97), (84, 97), (85, 97), (86, 97), (87, 97), (88, 97), (89, 97), (90, 97), (91, 97), (92, 97), (93, 97), (94, 97), (95, 97), (96, 97), (5, 96), (6, 96), (7, 96), (8, 96), (9, 96), (10, 96), (11, 96), (12, 96), (13, 96), (14, 96), (15, 96), (16, 96), (17, 96), (18, 96), (19, 96), (20, 96), (21, 96), (22, 96), (23, 96), (24, 96), (25, 96), (26, 96), (27, 96), (28, 96), (29, 96), (30, 96), (31, 96), (32, 96), (33, 96), (34, 96), (35, 96), (36, 96), (37, 96), (38, 96), (39, 96), (40, 96), (41, 96), (42, 96), (43, 96), (44, 96), (45, 96), (46, 96), (47, 96), (48, 96), (49, 96), (50, 96), (51, 96), (52, 96), (53, 96), (54, 96), (55, 96), (56, 96), (57, 96), (58, 96), (59, 96), (60, 96), (61, 96), (62, 96), (63, 96), (64, 96), (65, 96), (66, 96), (67, 96), (68, 96), (69, 96), (70, 96), (71, 96), (72, 96), (73, 96), (74, 96), (75, 96), (76, 96), (77, 96), (78, 96), (79, 96), (80, 96), (81, 96), (82, 96), (83, 96), (84, 96), (85, 96), (86, 96), (87, 96), (88, 96), (89, 96), (90, 96), (91, 96), (92, 96), (93, 96), (94, 96), (95, 96), (6, 95), (7, 95), (8, 95), (9, 95), (10, 95), (11, 95), (12, 95), (13, 95), (14, 95), (15, 95), (16, 95), (17, 95), (18, 95), (19, 95), (20, 95), (21, 95), (22, 95), (23, 95), (24, 95), (25, 95), (26, 95), (27, 95), (28, 95), (29, 95), (30, 95), (31, 95), (32, 95), (33, 95), (34, 95), (35, 95), (36, 95), (37, 95), (38, 95), (39, 95), (40, 95), (41, 95), (42, 95), (43, 95), (44, 95), (45, 95), (46, 95), (47, 95), (48, 95), (49, 95), (50, 95), (51, 95), (52, 95), (53, 95), (54, 95), (55, 95), (56, 95), (57, 95), (58, 95), (59, 95), (60, 95), (61, 95), (62, 95), (63, 95), (64, 95), (65, 95), (66, 95), (67, 95), (68, 95), (69, 95), (70, 95), (71, 95), (72, 95), (73, 95), (74, 95), (75, 95), (76, 95), (77, 95), (78, 95), (79, 95), (80, 95), (81, 95), (82, 95), (83, 95), (84, 95), (85, 95), (86, 95), (87, 95), (88, 95), (89, 95), (90, 95), (91, 95), (92, 95), (93, 95), (94, 95), (7, 94), (8, 94), (9, 94), (10, 94), (11, 94), (12, 94), (13, 94), (14, 94), (15, 94), (16, 94), (17, 94), (18, 94), (19, 94), (20, 94), (21, 94), (22, 94), (23, 94), (24, 94), (25, 94), (26, 94), (27, 94), (28, 94), (29, 94), (30, 94), (31, 94), (32, 94), (33, 94), (34, 94), (35, 94), (36, 94), (37, 94), (38, 94), (39, 94), (40, 94), (41, 94), (42, 94), (43, 94), (44, 94), (45, 94), (46, 94), (47, 94), (48, 94), (49, 94), (50, 94), (51, 94), (52, 94), (53, 94), (54, 94), (55, 94), (56, 94), (57, 94), (58, 94), (59, 94), (60, 94), (61, 94), (62, 94), (63, 94), (64, 94), (65, 94), (66, 94), (67, 94), (68, 94), (69, 94), (70, 94), (71, 94), (72, 94), (73, 94), (74, 94), (75, 94), (76, 94), (77, 94), (78, 94), (79, 94), (80, 94), (81, 94), (82, 94), (83, 94), (84, 94), (85, 94), (86, 94), (87, 94), (88, 94), (89, 94), (90, 94), (91, 94), (92, 94), (93, 94), (8, 93), (9, 93), (10, 93), (11, 93), (12, 93), (13, 93), (14, 93), (15, 93), (16, 93), (17, 93), (18, 93), (19, 93), (20, 93), (21, 93), (22, 93), (23, 93), (24, 93), (25, 93), (26, 93), (27, 93), (28, 93), (29, 93), (30, 93), (31, 93), (32, 93), (33, 93), (34, 93), (35, 93), (36, 93), (37, 93), (38, 93), (39, 93), (40, 93), (41, 93), (42, 93), (43, 93), (44, 93), (45, 93), (46, 93), (47, 93), (48, 93), (49, 93), (50, 93), (51, 93), (52, 93), (53, 93), (54, 93), (55, 93), (56, 93), (57, 93), (58, 93), (59, 93), (60, 93), (61, 93), (62, 93), (63, 93), (64, 93), (65, 93), (66, 93), (67, 93), (68, 93), (69, 93), (70, 93), (71, 93), (72, 93), (73, 93), (74, 93), (75, 93), (76, 93), (77, 93), (78, 93), (79, 93), (80, 93), (81, 93), (82, 93), (83, 93), (84, 93), (85, 93), (86, 93), (87, 93), (88, 93), (89, 93), (90, 93), (91, 93), (92, 93), (9, 92), (10, 92), (11, 92), (12, 92), (13, 92), (14, 92), (15, 92), (16, 92), (17, 92), (18, 92), (19, 92), (20, 92), (21, 92), (22, 92), (23, 92), (24, 92), (25, 92), (26, 92), (27, 92), (28, 92), (29, 92), (30, 92), (31, 92), (32, 92), (33, 92), (34, 92), (35, 92), (36, 92), (37, 92), (38, 92), (39, 92), (40, 92), (41, 92), (42, 92), (43, 92), (44, 92), (45, 92), (46, 92), (47, 92), (48, 92), (49, 92), (50, 92), (51, 92), (52, 92), (53, 92), (54, 92), (55, 92), (56, 92), (57, 92), (58, 92), (59, 92), (60, 92), (61, 92), (62, 92), (63, 92), (64, 92), (65, 92), (66, 92), (67, 92), (68, 92), (69, 92), (70, 92), (71, 92), (72, 92), (73, 92), (74, 92), (75, 92), (76, 92), (77, 92), (78, 92), (79, 92), (80, 92), (81, 92), (82, 92), (83, 92), (84, 92), (85, 92), (86, 92), (87, 92), (88, 92), (89, 92), (90, 92), (91, 92), (10, 91), (11, 91), (12, 91), (13, 91), (14, 91), (15, 91), (16, 91), (17, 91), (18, 91), (19, 91), (20, 91), (21, 91), (22, 91), (23, 91), (24, 91), (25, 91), (26, 91), (27, 91), (28, 91), (29, 91), (30, 91), (31, 91), (32, 91), (33, 91), (34, 91), (35, 91), (36, 91), (37, 91), (38, 91), (39, 91), (40, 91), (41, 91), (42, 91), (43, 91), (44, 91), (45, 91), (46, 91), (47, 91), (48, 91), (49, 91), (50, 91), (51, 91), (52, 91), (53, 91), (54, 91), (55, 91), (56, 91), (57, 91), (58, 91), (59, 91), (60, 91), (61, 91), (62, 91), (63, 91), (64, 91), (65, 91), (66, 91), (67, 91), (68, 91), (69, 91), (70, 91), (71, 91), (72, 91), (73, 91), (74, 91), (75, 91), (76, 91), (77, 91), (78, 91), (79, 91), (80, 91), (81, 91), (82, 91), (83, 91), (84, 91), (85, 91), (86, 91), (87, 91), (88, 91), (89, 91), (90, 91), (11, 90), (12, 90), (13, 90), (14, 90), (15, 90), (16, 90), (17, 90), (18, 90), (19, 90), (20, 90), (21, 90), (22, 90), (23, 90), (24, 90), (25, 90), (26, 90), (27, 90), (28, 90), (29, 90), (30, 90), (31, 90), (32, 90), (33, 90), (34, 90), (35, 90), (36, 90), (37, 90), (38, 90), (39, 90), (40, 90), (41, 90), (42, 90), (43, 90), (44, 90), (45, 90), (46, 90), (47, 90), (48, 90), (49, 90), (50, 90), (51, 90), (52, 90), (53, 90), (54, 90), (55, 90), (56, 90), (57, 90), (58, 90), (59, 90), (60, 90), (61, 90), (62, 90), (63, 90), (64, 90), (65, 90), (66, 90), (67, 90), (68, 90), (69, 90), (70, 90), (71, 90), (72, 90), (73, 90), (74, 90), (75, 90), (76, 90), (77, 90), (78, 90), (79, 90), (80, 90), (81, 90), (82, 90), (83, 90), (84, 90), (85, 90), (86, 90), (87, 90), (88, 90), (89, 90), (12, 89), (13, 89), (14, 89), (15, 89), (16, 89), (17, 89), (18, 89), (19, 89), (20, 89), (21, 89), (22, 89), (23, 89), (24, 89), (25, 89), (26, 89), (27, 89), (28, 89), (29, 89), (30, 89), (31, 89), (32, 89), (33, 89), (34, 89), (35, 89), (36, 89), (37, 89), (38, 89), (39, 89), (40, 89), (41, 89), (42, 89), (43, 89), (44, 89), (45, 89), (46, 89), (47, 89), (48, 89), (49, 89), (50, 89), (51, 89), (52, 89), (53, 89), (54, 89), (55, 89), (56, 89), (57, 89), (58, 89), (59, 89), (60, 89), (61, 89), (62, 89), (63, 89), (64, 89), (65, 89), (66, 89), (67, 89), (68, 89), (69, 89), (70, 89), (71, 89), (72, 89), (73, 89), (74, 89), (75, 89), (76, 89), (77, 89), (78, 89), (79, 89), (80, 89), (81, 89), (82, 89), (83, 89), (84, 89), (85, 89), (86, 89), (87, 89), (88, 89), (13, 88), (14, 88), (15, 88), (16, 88), (17, 88), (18, 88), (19, 88), (20, 88), (21, 88), (22, 88), (23, 88), (24, 88), (25, 88), (26, 88), (27, 88), (28, 88), (29, 88), (30, 88), (31, 88), (32, 88), (33, 88), (34, 88), (35, 88), (36, 88), (37, 88), (38, 88), (39, 88), (40, 88), (41, 88), (42, 88), (43, 88), (44, 88), (45, 88), (46, 88), (47, 88), (48, 88), (49, 88), (50, 88), (51, 88), (52, 88), (53, 88), (54, 88), (55, 88), (56, 88), (57, 88), (58, 88), (59, 88), (60, 88), (61, 88), (62, 88), (63, 88), (64, 88), (65, 88), (66, 88), (67, 88), (68, 88), (69, 88), (70, 88), (71, 88), (72, 88), (73, 88), (74, 88), (75, 88), (76, 88), (77, 88), (78, 88), (79, 88), (80, 88), (81, 88), (82, 88), (83, 88), (84, 88), (85, 88), (86, 88), (87, 88), (14, 87), (15, 87), (16, 87), (17, 87), (18, 87), (19, 87), (20, 87), (21, 87), (22, 87), (23, 87), (24, 87), (25, 87), (26, 87), (27, 87), (28, 87), (29, 87), (30, 87), (31, 87), (32, 87), (33, 87), (34, 87), (35, 87), (36, 87), (37, 87), (38, 87), (39, 87), (40, 87), (41, 87), (42, 87), (43, 87), (44, 87), (45, 87), (46, 87), (47, 87), (48, 87), (49, 87), (50, 87), (51, 87), (52, 87), (53, 87), (54, 87), (55, 87), (56, 87), (57, 87), (58, 87), (59, 87), (60, 87), (61, 87), (62, 87), (63, 87), (64, 87), (65, 87), (66, 87), (67, 87), (68, 87), (69, 87), (70, 87), (71, 87), (72, 87), (73, 87), (74, 87), (75, 87), (76, 87), (77, 87), (78, 87), (79, 87), (80, 87), (81, 87), (82, 87), (83, 87), (84, 87), (85, 87), (86, 87), (15, 86), (16, 86), (17, 86), (18, 86), (19, 86), (20, 86), (21, 86), (22, 86), (23, 86), (24, 86), (25, 86), (26, 86), (27, 86), (28, 86), (29, 86), (30, 86), (31, 86), (32, 86), (33, 86), (34, 86), (35, 86), (36, 86), (37, 86), (38, 86), (39, 86), (40, 86), (41, 86), (42, 86), (43, 86), (44, 86), (45, 86), (46, 86), (47, 86), (48, 86), (49, 86), (50, 86), (51, 86), (52, 86), (53, 86), (54, 86), (55, 86), (56, 86), (57, 86), (58, 86), (59, 86), (60, 86), (61, 86), (62, 86), (63, 86), (64, 86), (65, 86), (66, 86), (67, 86), (68, 86), (69, 86), (70, 86), (71, 86), (72, 86), (73, 86), (74, 86), (75, 86), (76, 86), (77, 86), (78, 86), (79, 86), (80, 86), (81, 86), (82, 86), (83, 86), (84, 86), (85, 86), (16, 85), (17, 85), (18, 85), (19, 85), (20, 85), (21, 85), (22, 85), (23, 85), (24, 85), (25, 85), (26, 85), (27, 85), (28, 85), (29, 85), (30, 85), (31, 85), (32, 85), (33, 85), (34, 85), (35, 85), (36, 85), (37, 85), (38, 85), (39, 85), (40, 85), (41, 85), (42, 85), (43, 85), (44, 85), (45, 85), (46, 85), (47, 85), (48, 85), (49, 85), (50, 85), (51, 85), (52, 85), (53, 85), (54, 85), (55, 85), (56, 85), (57, 85), (58, 85), (59, 85), (60, 85), (61, 85), (62, 85), (63, 85), (64, 85), (65, 85), (66, 85), (67, 85), (68, 85), (69, 85), (70, 85), (71, 85), (72, 85), (73, 85), (74, 85), (75, 85), (76, 85), (77, 85), (78, 85), (79, 85), (80, 85), (81, 85), (82, 85), (83, 85), (84, 85), (17, 84), (18, 84), (19, 84), (20, 84), (21, 84), (22, 84), (23, 84), (24, 84), (25, 84), (26, 84), (27, 84), (28, 84), (29, 84), (30, 84), (31, 84), (32, 84), (33, 84), (34, 84), (35, 84), (36, 84), (37, 84), (38, 84), (39, 84), (40, 84), (41, 84), (42, 84), (43, 84), (44, 84), (45, 84), (46, 84), (47, 84), (48, 84), (49, 84), (50, 84), (51, 84), (52, 84), (53, 84), (54, 84), (55, 84), (56, 84), (57, 84), (58, 84), (59, 84), (60, 84), (61, 84), (62, 84), (63, 84), (64, 84), (65, 84), (66, 84), (67, 84), (68, 84), (69, 84), (70, 84), (71, 84), (72, 84), (73, 84), (74, 84), (75, 84), (76, 84), (77, 84), (78, 84), (79, 84), (80, 84), (81, 84), (82, 84), (83, 84), (18, 83), (19, 83), (20, 83), (21, 83), (22, 83), (23, 83), (24, 83), (25, 83), (26, 83), (27, 83), (28, 83), (29, 83), (30, 83), (31, 83), (32, 83), (33, 83), (34, 83), (35, 83), (36, 83), (37, 83), (38, 83), (39, 83), (40, 83), (41, 83), (42, 83), (43, 83), (44, 83), (45, 83), (46, 83), (47, 83), (48, 83), (49, 83), (50, 83), (51, 83), (52, 83), (53, 83), (54, 83), (55, 83), (56, 83), (57, 83), (58, 83), (59, 83), (60, 83), (61, 83), (62, 83), (63, 83), (64, 83), (65, 83), (66, 83), (67, 83), (68, 83), (69, 83), (70, 83), (71, 83), (72, 83), (73, 83), (74, 83), (75, 83), (76, 83), (77, 83), (78, 83), (79, 83), (80, 83), (81, 83), (82, 83), (19, 82), (20, 82), (21, 82), (22, 82), (23, 82), (24, 82), (25, 82), (26, 82), (27, 82), (28, 82), (29, 82), (30, 82), (31, 82), (32, 82), (33, 82), (34, 82), (35, 82), (36, 82), (37, 82), (38, 82), (39, 82), (40, 82), (41, 82), (42, 82), (43, 82), (44, 82), (45, 82), (46, 82), (47, 82), (48, 82), (49, 82), (50, 82), (51, 82), (52, 82), (53, 82), (54, 82), (55, 82), (56, 82), (57, 82), (58, 82), (59, 82), (60, 82), (61, 82), (62, 82), (63, 82), (64, 82), (65, 82), (66, 82), (67, 82), (68, 82), (69, 82), (70, 82), (71, 82), (72, 82), (73, 82), (74, 82), (75, 82), (76, 82), (77, 82), (78, 82), (79, 82), (80, 82), (81, 82), (20, 81), (21, 81), (22, 81), (23, 81), (24, 81), (25, 81), (26, 81), (27, 81), (28, 81), (29, 81), (30, 81), (31, 81), (32, 81), (33, 81), (34, 81), (35, 81), (36, 81), (37, 81), (38, 81), (39, 81), (40, 81), (41, 81), (42, 81), (43, 81), (44, 81), (45, 81), (46, 81), (47, 81), (48, 81), (49, 81), (50, 81), (51, 81), (52, 81), (53, 81), (54, 81), (55, 81), (56, 81), (57, 81), (58, 81), (59, 81), (60, 81), (61, 81), (62, 81), (63, 81), (64, 81), (65, 81), (66, 81), (67, 81), (68, 81), (69, 81), (70, 81), (71, 81), (72, 81), (73, 81), (74, 81), (75, 81), (76, 81), (77, 81), (78, 81), (79, 81), (80, 81), (21, 80), (22, 80), (23, 80), (24, 80), (25, 80), (26, 80), (27, 80), (28, 80), (29, 80), (30, 80), (31, 80), (32, 80), (33, 80), (34, 80), (35, 80), (36, 80), (37, 80), (38, 80), (39, 80), (40, 80), (41, 80), (42, 80), (43, 80), (44, 80), (45, 80), (46, 80), (47, 80), (48, 80), (49, 80), (50, 80), (51, 80), (52, 80), (53, 80), (54, 80), (55, 80), (56, 80), (57, 80), (58, 80), (59, 80), (60, 80), (61, 80), (62, 80), (63, 80), (64, 80), (65, 80), (66, 80), (67, 80), (68, 80), (69, 80), (70, 80), (71, 80), (72, 80), (73, 80), (74, 80), (75, 80), (76, 80), (77, 80), (78, 80), (79, 80), (22, 79), (23, 79), (24, 79), (25, 79), (26, 79), (27, 79), (28, 79), (29, 79), (30, 79), (31, 79), (32, 79), (33, 79), (34, 79), (35, 79), (36, 79), (37, 79), (38, 79), (39, 79), (40, 79), (41, 79), (42, 79), (43, 79), (44, 79), (45, 79), (46, 79), (47, 79), (48, 79), (49, 79), (50, 79), (51, 79), (52, 79), (53, 79), (54, 79), (55, 79), (56, 79), (57, 79), (58, 79), (59, 79), (60, 79), (61, 79), (62, 79), (63, 79), (64, 79), (65, 79), (66, 79), (67, 79), (68, 79), (69, 79), (70, 79), (71, 79), (72, 79), (73, 79), (74, 79), (75, 79), (76, 79), (77, 79), (78, 79), (23, 78), (24, 78), (25, 78), (26, 78), (27, 78), (28, 78), (29, 78), (30, 78), (31, 78), (32, 78), (33, 78), (34, 78), (35, 78), (36, 78), (37, 78), (38, 78), (39, 78), (40, 78), (41, 78), (42, 78), (43, 78), (44, 78), (45, 78), (46, 78), (47, 78), (48, 78), (49, 78), (50, 78), (51, 78), (52, 78), (53, 78), (54, 78), (55, 78), (56, 78), (57, 78), (58, 78), (59, 78), (60, 78), (61, 78), (62, 78), (63, 78), (64, 78), (65, 78), (66, 78), (67, 78), (68, 78), (69, 78), (70, 78), (71, 78), (72, 78), (73, 78), (74, 78), (75, 78), (76, 78), (77, 78), (24, 77), (25, 77), (26, 77), (27, 77), (28, 77), (29, 77), (30, 77), (31, 77), (32, 77), (33, 77), (34, 77), (35, 77), (36, 77), (37, 77), (38, 77), (39, 77), (40, 77), (41, 77), (42, 77), (43, 77), (44, 77), (45, 77), (46, 77), (47, 77), (48, 77), (49, 77), (50, 77), (51, 77), (52, 77), (53, 77), (54, 77), (55, 77), (56, 77), (57, 77), (58, 77), (59, 77), (60, 77), (61, 77), (62, 77), (63, 77), (64, 77), (65, 77), (66, 77), (67, 77), (68, 77), (69, 77), (70, 77), (71, 77), (72, 77), (73, 77), (74, 77), (75, 77), (76, 77), (25, 76), (26, 76), (27, 76), (28, 76), (29, 76), (30, 76), (31, 76), (32, 76), (33, 76), (34, 76), (35, 76), (36, 76), (37, 76), (38, 76), (39, 76), (40, 76), (41, 76), (42, 76), (43, 76), (44, 76), (45, 76), (46, 76), (47, 76), (48, 76), (49, 76), (50, 76), (51, 76), (52, 76), (53, 76), (54, 76), (55, 76), (56, 76), (57, 76), (58, 76), (59, 76), (60, 76), (61, 76), (62, 76), (63, 76), (64, 76), (65, 76), (66, 76), (67, 76), (68, 76), (69, 76), (70, 76), (71, 76), (72, 76), (73, 76), (74, 76), (75, 76), (26, 75), (27, 75), (28, 75), (29, 75), (30, 75), (31, 75), (32, 75), (33, 75), (34, 75), (35, 75), (36, 75), (37, 75), (38, 75), (39, 75), (40, 75), (41, 75), (42, 75), (43, 75), (44, 75), (45, 75), (46, 75), (47, 75), (48, 75), (49, 75), (50, 75), (51, 75), (52, 75), (53, 75), (54, 75), (55, 75), (56, 75), (57, 75), (58, 75), (59, 75), (60, 75), (61, 75), (62, 75), (63, 75), (64, 75), (65, 75), (66, 75), (67, 75), (68, 75), (69, 75), (70, 75), (71, 75), (72, 75), (73, 75), (74, 75), (27, 74), (28, 74), (29, 74), (30, 74), (31, 74), (32, 74), (33, 74), (34, 74), (35, 74), (36, 74), (37, 74), (38, 74), (39, 74), (40, 74), (41, 74), (42, 74), (43, 74), (44, 74), (45, 74), (46, 74), (47, 74), (48, 74), (49, 74), (50, 74), (51, 74), (52, 74), (53, 74), (54, 74), (55, 74), (56, 74), (57, 74), (58, 74), (59, 74), (60, 74), (61, 74), (62, 74), (63, 74), (64, 74), (65, 74), (66, 74), (67, 74), (68, 74), (69, 74), (70, 74), (71, 74), (72, 74), (73, 74), (28, 73), (29, 73), (30, 73), (31, 73), (32, 73), (33, 73), (34, 73), (35, 73), (36, 73), (37, 73), (38, 73), (39, 73), (40, 73), (41, 73), (42, 73), (43, 73), (44, 73), (45, 73), (46, 73), (47, 73), (48, 73), (49, 73), (50, 73), (51, 73), (52, 73), (53, 73), (54, 73), (55, 73), (56, 73), (57, 73), (58, 73), (59, 73), (60, 73), (61, 73), (62, 73), (63, 73), (64, 73), (65, 73), (66, 73), (67, 73), (68, 73), (69, 73), (70, 73), (71, 73), (72, 73), (29, 72), (30, 72), (31, 72), (32, 72), (33, 72), (34, 72), (35, 72), (36, 72), (37, 72), (38, 72), (39, 72), (40, 72), (41, 72), (42, 72), (43, 72), (44, 72), (45, 72), (46, 72), (47, 72), (48, 72), (49, 72), (50, 72), (51, 72), (52, 72), (53, 72), (54, 72), (55, 72), (56, 72), (57, 72), (58, 72), (59, 72), (60, 72), (61, 72), (62, 72), (63, 72), (64, 72), (65, 72), (66, 72), (67, 72), (68, 72), (69, 72), (70, 72), (71, 72), (30, 71), (31, 71), (32, 71), (33, 71), (34, 71), (35, 71), (36, 71), (37, 71), (38, 71), (39, 71), (40, 71), (41, 71), (42, 71), (43, 71), (44, 71), (45, 71), (46, 71), (47, 71), (48, 71), (49, 71), (50, 71), (51, 71), (52, 71), (53, 71), (54, 71), (55, 71), (56, 71), (57, 71), (58, 71), (59, 71), (60, 71), (61, 71), (62, 71), (63, 71), (64, 71), (65, 71), (66, 71), (67, 71), (68, 71), (69, 71), (70, 71), (31, 70), (32, 70), (33, 70), (34, 70), (35, 70), (36, 70), (37, 70), (38, 70), (39, 70), (40, 70), (41, 70), (42, 70), (43, 70), (44, 70), (45, 70), (46, 70), (47, 70), (48, 70), (49, 70), (50, 70), (51, 70), (52, 70), (53, 70), (54, 70), (55, 70), (56, 70), (57, 70), (58, 70), (59, 70), (60, 70), (61, 70), (62, 70), (63, 70), (64, 70), (65, 70), (66, 70), (67, 70), (68, 70), (69, 70), (32, 69), (33, 69), (34, 69), (35, 69), (36, 69), (37, 69), (38, 69), (39, 69), (40, 69), (41, 69), (42, 69), (43, 69), (44, 69), (45, 69), (46, 69), (47, 69), (48, 69), (49, 69), (50, 69), (51, 69), (52, 69), (53, 69), (54, 69), (55, 69), (56, 69), (57, 69), (58, 69), (59, 69), (60, 69), (61, 69), (62, 69), (63, 69), (64, 69), (65, 69), (66, 69), (67, 69), (68, 69), (33, 68), (34, 68), (35, 68), (36, 68), (37, 68), (38, 68), (39, 68), (40, 68), (41, 68), (42, 68), (43, 68), (44, 68), (45, 68), (46, 68), (47, 68), (48, 68), (49, 68), (50, 68), (51, 68), (52, 68), (53, 68), (54, 68), (55, 68), (56, 68), (57, 68), (58, 68), (59, 68), (60, 68), (61, 68), (62, 68), (63, 68), (64, 68), (65, 68), (66, 68), (67, 68), (34, 67), (35, 67), (36, 67), (37, 67), (38, 67), (39, 67), (40, 67), (41, 67), (42, 67), (43, 67), (44, 67), (45, 67), (46, 67), (47, 67), (48, 67), (49, 67), (50, 67), (51, 67), (52, 67), (53, 67), (54, 67), (55, 67), (56, 67), (57, 67), (58, 67), (59, 67), (60, 67), (61, 67), (62, 67), (63, 67), (64, 67), (65, 67), (66, 67), (35, 66), (36, 66), (37, 66), (38, 66), (39, 66), (40, 66), (41, 66), (42, 66), (43, 66), (44, 66), (45, 66), (46, 66), (47, 66), (48, 66), (49, 66), (50, 66), (51, 66), (52, 66), (53, 66), (54, 66), (55, 66), (56, 66), (57, 66), (58, 66), (59, 66), (60, 66), (61, 66), (62, 66), (63, 66), (64, 66), (65, 66), (36, 65), (37, 65), (38, 65), (39, 65), (40, 65), (41, 65), (42, 65), (43, 65), (44, 65), (45, 65), (46, 65), (47, 65), (48, 65), (49, 65), (50, 65), (51, 65), (52, 65), (53, 65), (54, 65), (55, 65), (56, 65), (57, 65), (58, 65), (59, 65), (60, 65), (61, 65), (62, 65), (63, 65), (64, 65), (37, 64), (38, 64), (39, 64), (40, 64), (41, 64), (42, 64), (43, 64), (44, 64), (45, 64), (46, 64), (47, 64), (48, 64), (49, 64), (50, 64), (51, 64), (52, 64), (53, 64), (54, 64), (55, 64), (56, 64), (57, 64), (58, 64), (59, 64), (60, 64), (61, 64), (62, 64), (63, 64), (38, 63), (39, 63), (40, 63), (41, 63), (42, 63), (43, 63), (44, 63), (45, 63), (46, 63), (47, 63), (48, 63), (49, 63), (50, 63), (51, 63), (52, 63), (53, 63), (54, 63), (55, 63), (56, 63), (57, 63), (58, 63), (59, 63), (60, 63), (61, 63), (62, 63), (39, 62), (40, 62), (41, 62), (42, 62), (43, 62), (44, 62), (45, 62), (46, 62), (47, 62), (48, 62), (49, 62), (50, 62), (51, 62), (52, 62), (53, 62), (54, 62), (55, 62), (56, 62), (57, 62), (58, 62), (59, 62), (60, 62), (61, 62), (40, 61), (41, 61), (42, 61), (43, 61), (44, 61), (45, 61), (46, 61), (47, 61), (48, 61), (49, 61), (50, 61), (51, 61), (52, 61), (53, 61), (54, 61), (55, 61), (56, 61), (57, 61), (58, 61), (59, 61), (60, 61), (41, 60), (42, 60), (43, 60), (44, 60), (45, 60), (46, 60), (47, 60), (48, 60), (49, 60), (50, 60), (51, 60), (52, 60), (53, 60), (54, 60), (55, 60), (56, 60), (57, 60), (58, 60), (59, 60), (42, 59), (43, 59), (44, 59), (45, 59), (46, 59), (47, 59), (48, 59), (49, 59), (50, 59), (51, 59), (52, 59), (53, 59), (54, 59), (55, 59), (56, 59), (57, 59), (58, 59), (43, 58), (44, 58), (45, 58), (46, 58), (47, 58), (48, 58), (49, 58), (50, 58), (51, 58), (52, 58), (53, 58), (54, 58), (55, 58), (56, 58), (57, 58), (44, 57), (45, 57), (46, 57), (47, 57), (48, 57), (49, 57), (50, 57), (51, 57), (52, 57), (53, 57), (54, 57), (55, 57), (56, 57), (45, 56), (46, 56), (47, 56), (48, 56), (49, 56), (50, 56), (51, 56), (52, 56), (53, 56), (54, 56), (55, 56), (46, 55), (47, 55), (48, 55), (49, 55), (50, 55), (51, 55), (52, 55), (53, 55), (54, 55), (47, 54), (48, 54), (49, 54), (50, 54), (51, 54), (52, 54), (53, 54), (48, 53), (49, 53), (50, 53), (51, 53), (52, 53), (49, 52), (50, 52), (51, 52), (50, 51), (99, 1), (99, 2), (99, 3), (99, 4), (99, 5), (99, 6), (99, 7), (99, 8), (99, 9), (99, 10), (99, 11), (99, 12), (99, 13), (99, 14), (99, 15), (99, 16), (99, 17), (99, 18), (99, 19), (99, 20), (99, 21), (99, 22), (99, 23), (99, 24), (99, 25), (99, 26), (99, 27), (99, 28), (99, 29), (99, 30), (99, 31), (99, 32), (99, 33), (99, 34), (99, 35), (99, 36), (99, 37), (99, 38), (99, 39), (99, 40), (99, 41), (99, 42), (99, 43), (99, 44), (99, 45), (99, 46), (99, 47), (99, 48), (99, 49), (99, 50), (99, 51), (99, 52), (99, 53), (99, 54), (99, 55), (99, 56), (99, 57), (99, 58), (99, 59), (99, 60), (99, 61), (99, 62), (99, 63), (99, 64), (99, 65), (99, 66), (99, 67), (99, 68), (99, 69), (99, 70), (99, 71), (99, 72), (99, 73), (99, 74), (99, 75), (99, 76), (99, 77), (99, 78), (99, 79), (99, 80), (99, 81), (99, 82), (99, 83), (99, 84), (99, 85), (99, 86), (99, 87), (99, 88), (99, 89), (99, 90), (99, 91), (99, 92), (99, 93), (99, 94), (99, 95), (99, 96), (99, 97), (99, 98), (98, 2), (98, 3), (98, 4), (98, 5), (98, 6), (98, 7), (98, 8), (98, 9), (98, 10), (98, 11), (98, 12), (98, 13), (98, 14), (98, 15), (98, 16), (98, 17), (98, 18), (98, 19), (98, 20), (98, 21), (98, 22), (98, 23), (98, 24), (98, 25), (98, 26), (98, 27), (98, 28), (98, 29), (98, 30), (98, 31), (98, 32), (98, 33), (98, 34), (98, 35), (98, 36), (98, 37), (98, 38), (98, 39), (98, 40), (98, 41), (98, 42), (98, 43), (98, 44), (98, 45), (98, 46), (98, 47), (98, 48), (98, 49), (98, 50), (98, 51), (98, 52), (98, 53), (98, 54), (98, 55), (98, 56), (98, 57), (98, 58), (98, 59), (98, 60), (98, 61), (98, 62), (98, 63), (98, 64), (98, 65), (98, 66), (98, 67), (98, 68), (98, 69), (98, 70), (98, 71), (98, 72), (98, 73), (98, 74), (98, 75), (98, 76), (98, 77), (98, 78), (98, 79), (98, 80), (98, 81), (98, 82), (98, 83), (98, 84), (98, 85), (98, 86), (98, 87), (98, 88), (98, 89), (98, 90), (98, 91), (98, 92), (98, 93), (98, 94), (98, 95), (98, 96), (98, 97), (97, 3), (97, 4), (97, 5), (97, 6), (97, 7), (97, 8), (97, 9), (97, 10), (97, 11), (97, 12), (97, 13), (97, 14), (97, 15), (97, 16), (97, 17), (97, 18), (97, 19), (97, 20), (97, 21), (97, 22), (97, 23), (97, 24), (97, 25), (97, 26), (97, 27), (97, 28), (97, 29), (97, 30), (97, 31), (97, 32), (97, 33), (97, 34), (97, 35), (97, 36), (97, 37), (97, 38), (97, 39), (97, 40), (97, 41), (97, 42), (97, 43), (97, 44), (97, 45), (97, 46), (97, 47), (97, 48), (97, 49), (97, 50), (97, 51), (97, 52), (97, 53), (97, 54), (97, 55), (97, 56), (97, 57), (97, 58), (97, 59), (97, 60), (97, 61), (97, 62), (97, 63), (97, 64), (97, 65), (97, 66), (97, 67), (97, 68), (97, 69), (97, 70), (97, 71), (97, 72), (97, 73), (97, 74), (97, 75), (97, 76), (97, 77), (97, 78), (97, 79), (97, 80), (97, 81), (97, 82), (97, 83), (97, 84), (97, 85), (97, 86), (97, 87), (97, 88), (97, 89), (97, 90), (97, 91), (97, 92), (97, 93), (97, 94), (97, 95), (97, 96), (96, 4), (96, 5), (96, 6), (96, 7), (96, 8), (96, 9), (96, 10), (96, 11), (96, 12), (96, 13), (96, 14), (96, 15), (96, 16), (96, 17), (96, 18), (96, 19), (96, 20), (96, 21), (96, 22), (96, 23), (96, 24), (96, 25), (96, 26), (96, 27), (96, 28), (96, 29), (96, 30), (96, 31), (96, 32), (96, 33), (96, 34), (96, 35), (96, 36), (96, 37), (96, 38), (96, 39), (96, 40), (96, 41), (96, 42), (96, 43), (96, 44), (96, 45), (96, 46), (96, 47), (96, 48), (96, 49), (96, 50), (96, 51), (96, 52), (96, 53), (96, 54), (96, 55), (96, 56), (96, 57), (96, 58), (96, 59), (96, 60), (96, 61), (96, 62), (96, 63), (96, 64), (96, 65), (96, 66), (96, 67), (96, 68), (96, 69), (96, 70), (96, 71), (96, 72), (96, 73), (96, 74), (96, 75), (96, 76), (96, 77), (96, 78), (96, 79), (96, 80), (96, 81), (96, 82), (96, 83), (96, 84), (96, 85), (96, 86), (96, 87), (96, 88), (96, 89), (96, 90), (96, 91), (96, 92), (96, 93), (96, 94), (96, 95), (95, 5), (95, 6), (95, 7), (95, 8), (95, 9), (95, 10), (95, 11), (95, 12), (95, 13), (95, 14), (95, 15), (95, 16), (95, 17), (95, 18), (95, 19), (95, 20), (95, 21), (95, 22), (95, 23), (95, 24), (95, 25), (95, 26), (95, 27), (95, 28), (95, 29), (95, 30), (95, 31), (95, 32), (95, 33), (95, 34), (95, 35), (95, 36), (95, 37), (95, 38), (95, 39), (95, 40), (95, 41), (95, 42), (95, 43), (95, 44), (95, 45), (95, 46), (95, 47), (95, 48), (95, 49), (95, 50), (95, 51), (95, 52), (95, 53), (95, 54), (95, 55), (95, 56), (95, 57), (95, 58), (95, 59), (95, 60), (95, 61), (95, 62), (95, 63), (95, 64), (95, 65), (95, 66), (95, 67), (95, 68), (95, 69), (95, 70), (95, 71), (95, 72), (95, 73), (95, 74), (95, 75), (95, 76), (95, 77), (95, 78), (95, 79), (95, 80), (95, 81), (95, 82), (95, 83), (95, 84), (95, 85), (95, 86), (95, 87), (95, 88), (95, 89), (95, 90), (95, 91), (95, 92), (95, 93), (95, 94), (94, 6), (94, 7), (94, 8), (94, 9), (94, 10), (94, 11), (94, 12), (94, 13), (94, 14), (94, 15), (94, 16), (94, 17), (94, 18), (94, 19), (94, 20), (94, 21), (94, 22), (94, 23), (94, 24), (94, 25), (94, 26), (94, 27), (94, 28), (94, 29), (94, 30), (94, 31), (94, 32), (94, 33), (94, 34), (94, 35), (94, 36), (94, 37), (94, 38), (94, 39), (94, 40), (94, 41), (94, 42), (94, 43), (94, 44), (94, 45), (94, 46), (94, 47), (94, 48), (94, 49), (94, 50), (94, 51), (94, 52), (94, 53), (94, 54), (94, 55), (94, 56), (94, 57), (94, 58), (94, 59), (94, 60), (94, 61), (94, 62), (94, 63), (94, 64), (94, 65), (94, 66), (94, 67), (94, 68), (94, 69), (94, 70), (94, 71), (94, 72), (94, 73), (94, 74), (94, 75), (94, 76), (94, 77), (94, 78), (94, 79), (94, 80), (94, 81), (94, 82), (94, 83), (94, 84), (94, 85), (94, 86), (94, 87), (94, 88), (94, 89), (94, 90), (94, 91), (94, 92), (94, 93), (93, 7), (93, 8), (93, 9), (93, 10), (93, 11), (93, 12), (93, 13), (93, 14), (93, 15), (93, 16), (93, 17), (93, 18), (93, 19), (93, 20), (93, 21), (93, 22), (93, 23), (93, 24), (93, 25), (93, 26), (93, 27), (93, 28), (93, 29), (93, 30), (93, 31), (93, 32), (93, 33), (93, 34), (93, 35), (93, 36), (93, 37), (93, 38), (93, 39), (93, 40), (93, 41), (93, 42), (93, 43), (93, 44), (93, 45), (93, 46), (93, 47), (93, 48), (93, 49), (93, 50), (93, 51), (93, 52), (93, 53), (93, 54), (93, 55), (93, 56), (93, 57), (93, 58), (93, 59), (93, 60), (93, 61), (93, 62), (93, 63), (93, 64), (93, 65), (93, 66), (93, 67), (93, 68), (93, 69), (93, 70), (93, 71), (93, 72), (93, 73), (93, 74), (93, 75), (93, 76), (93, 77), (93, 78), (93, 79), (93, 80), (93, 81), (93, 82), (93, 83), (93, 84), (93, 85), (93, 86), (93, 87), (93, 88), (93, 89), (93, 90), (93, 91), (93, 92), (92, 8), (92, 9), (92, 10), (92, 11), (92, 12), (92, 13), (92, 14), (92, 15), (92, 16), (92, 17), (92, 18), (92, 19), (92, 20), (92, 21), (92, 22), (92, 23), (92, 24), (92, 25), (92, 26), (92, 27), (92, 28), (92, 29), (92, 30), (92, 31), (92, 32), (92, 33), (92, 34), (92, 35), (92, 36), (92, 37), (92, 38), (92, 39), (92, 40), (92, 41), (92, 42), (92, 43), (92, 44), (92, 45), (92, 46), (92, 47), (92, 48), (92, 49), (92, 50), (92, 51), (92, 52), (92, 53), (92, 54), (92, 55), (92, 56), (92, 57), (92, 58), (92, 59), (92, 60), (92, 61), (92, 62), (92, 63), (92, 64), (92, 65), (92, 66), (92, 67), (92, 68), (92, 69), (92, 70), (92, 71), (92, 72), (92, 73), (92, 74), (92, 75), (92, 76), (92, 77), (92, 78), (92, 79), (92, 80), (92, 81), (92, 82), (92, 83), (92, 84), (92, 85), (92, 86), (92, 87), (92, 88), (92, 89), (92, 90), (92, 91), (91, 9), (91, 10), (91, 11), (91, 12), (91, 13), (91, 14), (91, 15), (91, 16), (91, 17), (91, 18), (91, 19), (91, 20), (91, 21), (91, 22), (91, 23), (91, 24), (91, 25), (91, 26), (91, 27), (91, 28), (91, 29), (91, 30), (91, 31), (91, 32), (91, 33), (91, 34), (91, 35), (91, 36), (91, 37), (91, 38), (91, 39), (91, 40), (91, 41), (91, 42), (91, 43), (91, 44), (91, 45), (91, 46), (91, 47), (91, 48), (91, 49), (91, 50), (91, 51), (91, 52), (91, 53), (91, 54), (91, 55), (91, 56), (91, 57), (91, 58), (91, 59), (91, 60), (91, 61), (91, 62), (91, 63), (91, 64), (91, 65), (91, 66), (91, 67), (91, 68), (91, 69), (91, 70), (91, 71), (91, 72), (91, 73), (91, 74), (91, 75), (91, 76), (91, 77), (91, 78), (91, 79), (91, 80), (91, 81), (91, 82), (91, 83), (91, 84), (91, 85), (91, 86), (91, 87), (91, 88), (91, 89), (91, 90), (90, 10), (90, 11), (90, 12), (90, 13), (90, 14), (90, 15), (90, 16), (90, 17), (90, 18), (90, 19), (90, 20), (90, 21), (90, 22), (90, 23), (90, 24), (90, 25), (90, 26), (90, 27), (90, 28), (90, 29), (90, 30), (90, 31), (90, 32), (90, 33), (90, 34), (90, 35), (90, 36), (90, 37), (90, 38), (90, 39), (90, 40), (90, 41), (90, 42), (90, 43), (90, 44), (90, 45), (90, 46), (90, 47), (90, 48), (90, 49), (90, 50), (90, 51), (90, 52), (90, 53), (90, 54), (90, 55), (90, 56), (90, 57), (90, 58), (90, 59), (90, 60), (90, 61), (90, 62), (90, 63), (90, 64), (90, 65), (90, 66), (90, 67), (90, 68), (90, 69), (90, 70), (90, 71), (90, 72), (90, 73), (90, 74), (90, 75), (90, 76), (90, 77), (90, 78), (90, 79), (90, 80), (90, 81), (90, 82), (90, 83), (90, 84), (90, 85), (90, 86), (90, 87), (90, 88), (90, 89), (89, 11), (89, 12), (89, 13), (89, 14), (89, 15), (89, 16), (89, 17), (89, 18), (89, 19), (89, 20), (89, 21), (89, 22), (89, 23), (89, 24), (89, 25), (89, 26), (89, 27), (89, 28), (89, 29), (89, 30), (89, 31), (89, 32), (89, 33), (89, 34), (89, 35), (89, 36), (89, 37), (89, 38), (89, 39), (89, 40), (89, 41), (89, 42), (89, 43), (89, 44), (89, 45), (89, 46), (89, 47), (89, 48), (89, 49), (89, 50), (89, 51), (89, 52), (89, 53), (89, 54), (89, 55), (89, 56), (89, 57), (89, 58), (89, 59), (89, 60), (89, 61), (89, 62), (89, 63), (89, 64), (89, 65), (89, 66), (89, 67), (89, 68), (89, 69), (89, 70), (89, 71), (89, 72), (89, 73), (89, 74), (89, 75), (89, 76), (89, 77), (89, 78), (89, 79), (89, 80), (89, 81), (89, 82), (89, 83), (89, 84), (89, 85), (89, 86), (89, 87), (89, 88), (88, 12), (88, 13), (88, 14), (88, 15), (88, 16), (88, 17), (88, 18), (88, 19), (88, 20), (88, 21), (88, 22), (88, 23), (88, 24), (88, 25), (88, 26), (88, 27), (88, 28), (88, 29), (88, 30), (88, 31), (88, 32), (88, 33), (88, 34), (88, 35), (88, 36), (88, 37), (88, 38), (88, 39), (88, 40), (88, 41), (88, 42), (88, 43), (88, 44), (88, 45), (88, 46), (88, 47), (88, 48), (88, 49), (88, 50), (88, 51), (88, 52), (88, 53), (88, 54), (88, 55), (88, 56), (88, 57), (88, 58), (88, 59), (88, 60), (88, 61), (88, 62), (88, 63), (88, 64), (88, 65), (88, 66), (88, 67), (88, 68), (88, 69), (88, 70), (88, 71), (88, 72), (88, 73), (88, 74), (88, 75), (88, 76), (88, 77), (88, 78), (88, 79), (88, 80), (88, 81), (88, 82), (88, 83), (88, 84), (88, 85), (88, 86), (88, 87), (87, 13), (87, 14), (87, 15), (87, 16), (87, 17), (87, 18), (87, 19), (87, 20), (87, 21), (87, 22), (87, 23), (87, 24), (87, 25), (87, 26), (87, 27), (87, 28), (87, 29), (87, 30), (87, 31), (87, 32), (87, 33), (87, 34), (87, 35), (87, 36), (87, 37), (87, 38), (87, 39), (87, 40), (87, 41), (87, 42), (87, 43), (87, 44), (87, 45), (87, 46), (87, 47), (87, 48), (87, 49), (87, 50), (87, 51), (87, 52), (87, 53), (87, 54), (87, 55), (87, 56), (87, 57), (87, 58), (87, 59), (87, 60), (87, 61), (87, 62), (87, 63), (87, 64), (87, 65), (87, 66), (87, 67), (87, 68), (87, 69), (87, 70), (87, 71), (87, 72), (87, 73), (87, 74), (87, 75), (87, 76), (87, 77), (87, 78), (87, 79), (87, 80), (87, 81), (87, 82), (87, 83), (87, 84), (87, 85), (87, 86), (86, 14), (86, 15), (86, 16), (86, 17), (86, 18), (86, 19), (86, 20), (86, 21), (86, 22), (86, 23), (86, 24), (86, 25), (86, 26), (86, 27), (86, 28), (86, 29), (86, 30), (86, 31), (86, 32), (86, 33), (86, 34), (86, 35), (86, 36), (86, 37), (86, 38), (86, 39), (86, 40), (86, 41), (86, 42), (86, 43), (86, 44), (86, 45), (86, 46), (86, 47), (86, 48), (86, 49), (86, 50), (86, 51), (86, 52), (86, 53), (86, 54), (86, 55), (86, 56), (86, 57), (86, 58), (86, 59), (86, 60), (86, 61), (86, 62), (86, 63), (86, 64), (86, 65), (86, 66), (86, 67), (86, 68), (86, 69), (86, 70), (86, 71), (86, 72), (86, 73), (86, 74), (86, 75), (86, 76), (86, 77), (86, 78), (86, 79), (86, 80), (86, 81), (86, 82), (86, 83), (86, 84), (86, 85), (85, 15), (85, 16), (85, 17), (85, 18), (85, 19), (85, 20), (85, 21), (85, 22), (85, 23), (85, 24), (85, 25), (85, 26), (85, 27), (85, 28), (85, 29), (85, 30), (85, 31), (85, 32), (85, 33), (85, 34), (85, 35), (85, 36), (85, 37), (85, 38), (85, 39), (85, 40), (85, 41), (85, 42), (85, 43), (85, 44), (85, 45), (85, 46), (85, 47), (85, 48), (85, 49), (85, 50), (85, 51), (85, 52), (85, 53), (85, 54), (85, 55), (85, 56), (85, 57), (85, 58), (85, 59), (85, 60), (85, 61), (85, 62), (85, 63), (85, 64), (85, 65), (85, 66), (85, 67), (85, 68), (85, 69), (85, 70), (85, 71), (85, 72), (85, 73), (85, 74), (85, 75), (85, 76), (85, 77), (85, 78), (85, 79), (85, 80), (85, 81), (85, 82), (85, 83), (85, 84), (84, 16), (84, 17), (84, 18), (84, 19), (84, 20), (84, 21), (84, 22), (84, 23), (84, 24), (84, 25), (84, 26), (84, 27), (84, 28), (84, 29), (84, 30), (84, 31), (84, 32), (84, 33), (84, 34), (84, 35), (84, 36), (84, 37), (84, 38), (84, 39), (84, 40), (84, 41), (84, 42), (84, 43), (84, 44), (84, 45), (84, 46), (84, 47), (84, 48), (84, 49), (84, 50), (84, 51), (84, 52), (84, 53), (84, 54), (84, 55), (84, 56), (84, 57), (84, 58), (84, 59), (84, 60), (84, 61), (84, 62), (84, 63), (84, 64), (84, 65), (84, 66), (84, 67), (84, 68), (84, 69), (84, 70), (84, 71), (84, 72), (84, 73), (84, 74), (84, 75), (84, 76), (84, 77), (84, 78), (84, 79), (84, 80), (84, 81), (84, 82), (84, 83), (83, 17), (83, 18), (83, 19), (83, 20), (83, 21), (83, 22), (83, 23), (83, 24), (83, 25), (83, 26), (83, 27), (83, 28), (83, 29), (83, 30), (83, 31), (83, 32), (83, 33), (83, 34), (83, 35), (83, 36), (83, 37), (83, 38), (83, 39), (83, 40), (83, 41), (83, 42), (83, 43), (83, 44), (83, 45), (83, 46), (83, 47), (83, 48), (83, 49), (83, 50), (83, 51), (83, 52), (83, 53), (83, 54), (83, 55), (83, 56), (83, 57), (83, 58), (83, 59), (83, 60), (83, 61), (83, 62), (83, 63), (83, 64), (83, 65), (83, 66), (83, 67), (83, 68), (83, 69), (83, 70), (83, 71), (83, 72), (83, 73), (83, 74), (83, 75), (83, 76), (83, 77), (83, 78), (83, 79), (83, 80), (83, 81), (83, 82), (82, 18), (82, 19), (82, 20), (82, 21), (82, 22), (82, 23), (82, 24), (82, 25), (82, 26), (82, 27), (82, 28), (82, 29), (82, 30), (82, 31), (82, 32), (82, 33), (82, 34), (82, 35), (82, 36), (82, 37), (82, 38), (82, 39), (82, 40), (82, 41), (82, 42), (82, 43), (82, 44), (82, 45), (82, 46), (82, 47), (82, 48), (82, 49), (82, 50), (82, 51), (82, 52), (82, 53), (82, 54), (82, 55), (82, 56), (82, 57), (82, 58), (82, 59), (82, 60), (82, 61), (82, 62), (82, 63), (82, 64), (82, 65), (82, 66), (82, 67), (82, 68), (82, 69), (82, 70), (82, 71), (82, 72), (82, 73), (82, 74), (82, 75), (82, 76), (82, 77), (82, 78), (82, 79), (82, 80), (82, 81), (81, 19), (81, 20), (81, 21), (81, 22), (81, 23), (81, 24), (81, 25), (81, 26), (81, 27), (81, 28), (81, 29), (81, 30), (81, 31), (81, 32), (81, 33), (81, 34), (81, 35), (81, 36), (81, 37), (81, 38), (81, 39), (81, 40), (81, 41), (81, 42), (81, 43), (81, 44), (81, 45), (81, 46), (81, 47), (81, 48), (81, 49), (81, 50), (81, 51), (81, 52), (81, 53), (81, 54), (81, 55), (81, 56), (81, 57), (81, 58), (81, 59), (81, 60), (81, 61), (81, 62), (81, 63), (81, 64), (81, 65), (81, 66), (81, 67), (81, 68), (81, 69), (81, 70), (81, 71), (81, 72), (81, 73), (81, 74), (81, 75), (81, 76), (81, 77), (81, 78), (81, 79), (81, 80), (80, 20), (80, 21), (80, 22), (80, 23), (80, 24), (80, 25), (80, 26), (80, 27), (80, 28), (80, 29), (80, 30), (80, 31), (80, 32), (80, 33), (80, 34), (80, 35), (80, 36), (80, 37), (80, 38), (80, 39), (80, 40), (80, 41), (80, 42), (80, 43), (80, 44), (80, 45), (80, 46), (80, 47), (80, 48), (80, 49), (80, 50), (80, 51), (80, 52), (80, 53), (80, 54), (80, 55), (80, 56), (80, 57), (80, 58), (80, 59), (80, 60), (80, 61), (80, 62), (80, 63), (80, 64), (80, 65), (80, 66), (80, 67), (80, 68), (80, 69), (80, 70), (80, 71), (80, 72), (80, 73), (80, 74), (80, 75), (80, 76), (80, 77), (80, 78), (80, 79), (79, 21), (79, 22), (79, 23), (79, 24), (79, 25), (79, 26), (79, 27), (79, 28), (79, 29), (79, 30), (79, 31), (79, 32), (79, 33), (79, 34), (79, 35), (79, 36), (79, 37), (79, 38), (79, 39), (79, 40), (79, 41), (79, 42), (79, 43), (79, 44), (79, 45), (79, 46), (79, 47), (79, 48), (79, 49), (79, 50), (79, 51), (79, 52), (79, 53), (79, 54), (79, 55), (79, 56), (79, 57), (79, 58), (79, 59), (79, 60), (79, 61), (79, 62), (79, 63), (79, 64), (79, 65), (79, 66), (79, 67), (79, 68), (79, 69), (79, 70), (79, 71), (79, 72), (79, 73), (79, 74), (79, 75), (79, 76), (79, 77), (79, 78), (78, 22), (78, 23), (78, 24), (78, 25), (78, 26), (78, 27), (78, 28), (78, 29), (78, 30), (78, 31), (78, 32), (78, 33), (78, 34), (78, 35), (78, 36), (78, 37), (78, 38), (78, 39), (78, 40), (78, 41), (78, 42), (78, 43), (78, 44), (78, 45), (78, 46), (78, 47), (78, 48), (78, 49), (78, 50), (78, 51), (78, 52), (78, 53), (78, 54), (78, 55), (78, 56), (78, 57), (78, 58), (78, 59), (78, 60), (78, 61), (78, 62), (78, 63), (78, 64), (78, 65), (78, 66), (78, 67), (78, 68), (78, 69), (78, 70), (78, 71), (78, 72), (78, 73), (78, 74), (78, 75), (78, 76), (78, 77), (77, 23), (77, 24), (77, 25), (77, 26), (77, 27), (77, 28), (77, 29), (77, 30), (77, 31), (77, 32), (77, 33), (77, 34), (77, 35), (77, 36), (77, 37), (77, 38), (77, 39), (77, 40), (77, 41), (77, 42), (77, 43), (77, 44), (77, 45), (77, 46), (77, 47), (77, 48), (77, 49), (77, 50), (77, 51), (77, 52), (77, 53), (77, 54), (77, 55), (77, 56), (77, 57), (77, 58), (77, 59), (77, 60), (77, 61), (77, 62), (77, 63), (77, 64), (77, 65), (77, 66), (77, 67), (77, 68), (77, 69), (77, 70), (77, 71), (77, 72), (77, 73), (77, 74), (77, 75), (77, 76), (76, 24), (76, 25), (76, 26), (76, 27), (76, 28), (76, 29), (76, 30), (76, 31), (76, 32), (76, 33), (76, 34), (76, 35), (76, 36), (76, 37), (76, 38), (76, 39), (76, 40), (76, 41), (76, 42), (76, 43), (76, 44), (76, 45), (76, 46), (76, 47), (76, 48), (76, 49), (76, 50), (76, 51), (76, 52), (76, 53), (76, 54), (76, 55), (76, 56), (76, 57), (76, 58), (76, 59), (76, 60), (76, 61), (76, 62), (76, 63), (76, 64), (76, 65), (76, 66), (76, 67), (76, 68), (76, 69), (76, 70), (76, 71), (76, 72), (76, 73), (76, 74), (76, 75), (75, 25), (75, 26), (75, 27), (75, 28), (75, 29), (75, 30), (75, 31), (75, 32), (75, 33), (75, 34), (75, 35), (75, 36), (75, 37), (75, 38), (75, 39), (75, 40), (75, 41), (75, 42), (75, 43), (75, 44), (75, 45), (75, 46), (75, 47), (75, 48), (75, 49), (75, 50), (75, 51), (75, 52), (75, 53), (75, 54), (75, 55), (75, 56), (75, 57), (75, 58), (75, 59), (75, 60), (75, 61), (75, 62), (75, 63), (75, 64), (75, 65), (75, 66), (75, 67), (75, 68), (75, 69), (75, 70), (75, 71), (75, 72), (75, 73), (75, 74), (74, 26), (74, 27), (74, 28), (74, 29), (74, 30), (74, 31), (74, 32), (74, 33), (74, 34), (74, 35), (74, 36), (74, 37), (74, 38), (74, 39), (74, 40), (74, 41), (74, 42), (74, 43), (74, 44), (74, 45), (74, 46), (74, 47), (74, 48), (74, 49), (74, 50), (74, 51), (74, 52), (74, 53), (74, 54), (74, 55), (74, 56), (74, 57), (74, 58), (74, 59), (74, 60), (74, 61), (74, 62), (74, 63), (74, 64), (74, 65), (74, 66), (74, 67), (74, 68), (74, 69), (74, 70), (74, 71), (74, 72), (74, 73), (73, 27), (73, 28), (73, 29), (73, 30), (73, 31), (73, 32), (73, 33), (73, 34), (73, 35), (73, 36), (73, 37), (73, 38), (73, 39), (73, 40), (73, 41), (73, 42), (73, 43), (73, 44), (73, 45), (73, 46), (73, 47), (73, 48), (73, 49), (73, 50), (73, 51), (73, 52), (73, 53), (73, 54), (73, 55), (73, 56), (73, 57), (73, 58), (73, 59), (73, 60), (73, 61), (73, 62), (73, 63), (73, 64), (73, 65), (73, 66), (73, 67), (73, 68), (73, 69), (73, 70), (73, 71), (73, 72), (72, 28), (72, 29), (72, 30), (72, 31), (72, 32), (72, 33), (72, 34), (72, 35), (72, 36), (72, 37), (72, 38), (72, 39), (72, 40), (72, 41), (72, 42), (72, 43), (72, 44), (72, 45), (72, 46), (72, 47), (72, 48), (72, 49), (72, 50), (72, 51), (72, 52), (72, 53), (72, 54), (72, 55), (72, 56), (72, 57), (72, 58), (72, 59), (72, 60), (72, 61), (72, 62), (72, 63), (72, 64), (72, 65), (72, 66), (72, 67), (72, 68), (72, 69), (72, 70), (72, 71), (71, 29), (71, 30), (71, 31), (71, 32), (71, 33), (71, 34), (71, 35), (71, 36), (71, 37), (71, 38), (71, 39), (71, 40), (71, 41), (71, 42), (71, 43), (71, 44), (71, 45), (71, 46), (71, 47), (71, 48), (71, 49), (71, 50), (71, 51), (71, 52), (71, 53), (71, 54), (71, 55), (71, 56), (71, 57), (71, 58), (71, 59), (71, 60), (71, 61), (71, 62), (71, 63), (71, 64), (71, 65), (71, 66), (71, 67), (71, 68), (71, 69), (71, 70), (70, 30), (70, 31), (70, 32), (70, 33), (70, 34), (70, 35), (70, 36), (70, 37), (70, 38), (70, 39), (70, 40), (70, 41), (70, 42), (70, 43), (70, 44), (70, 45), (70, 46), (70, 47), (70, 48), (70, 49), (70, 50), (70, 51), (70, 52), (70, 53), (70, 54), (70, 55), (70, 56), (70, 57), (70, 58), (70, 59), (70, 60), (70, 61), (70, 62), (70, 63), (70, 64), (70, 65), (70, 66), (70, 67), (70, 68), (70, 69), (69, 31), (69, 32), (69, 33), (69, 34), (69, 35), (69, 36), (69, 37), (69, 38), (69, 39), (69, 40), (69, 41), (69, 42), (69, 43), (69, 44), (69, 45), (69, 46), (69, 47), (69, 48), (69, 49), (69, 50), (69, 51), (69, 52), (69, 53), (69, 54), (69, 55), (69, 56), (69, 57), (69, 58), (69, 59), (69, 60), (69, 61), (69, 62), (69, 63), (69, 64), (69, 65), (69, 66), (69, 67), (69, 68), (68, 32), (68, 33), (68, 34), (68, 35), (68, 36), (68, 37), (68, 38), (68, 39), (68, 40), (68, 41), (68, 42), (68, 43), (68, 44), (68, 45), (68, 46), (68, 47), (68, 48), (68, 49), (68, 50), (68, 51), (68, 52), (68, 53), (68, 54), (68, 55), (68, 56), (68, 57), (68, 58), (68, 59), (68, 60), (68, 61), (68, 62), (68, 63), (68, 64), (68, 65), (68, 66), (68, 67), (67, 33), (67, 34), (67, 35), (67, 36), (67, 37), (67, 38), (67, 39), (67, 40), (67, 41), (67, 42), (67, 43), (67, 44), (67, 45), (67, 46), (67, 47), (67, 48), (67, 49), (67, 50), (67, 51), (67, 52), (67, 53), (67, 54), (67, 55), (67, 56), (67, 57), (67, 58), (67, 59), (67, 60), (67, 61), (67, 62), (67, 63), (67, 64), (67, 65), (67, 66), (66, 34), (66, 35), (66, 36), (66, 37), (66, 38), (66, 39), (66, 40), (66, 41), (66, 42), (66, 43), (66, 44), (66, 45), (66, 46), (66, 47), (66, 48), (66, 49), (66, 50), (66, 51), (66, 52), (66, 53), (66, 54), (66, 55), (66, 56), (66, 57), (66, 58), (66, 59), (66, 60), (66, 61), (66, 62), (66, 63), (66, 64), (66, 65), (65, 35), (65, 36), (65, 37), (65, 38), (65, 39), (65, 40), (65, 41), (65, 42), (65, 43), (65, 44), (65, 45), (65, 46), (65, 47), (65, 48), (65, 49), (65, 50), (65, 51), (65, 52), (65, 53), (65, 54), (65, 55), (65, 56), (65, 57), (65, 58), (65, 59), (65, 60), (65, 61), (65, 62), (65, 63), (65, 64), (64, 36), (64, 37), (64, 38), (64, 39), (64, 40), (64, 41), (64, 42), (64, 43), (64, 44), (64, 45), (64, 46), (64, 47), (64, 48), (64, 49), (64, 50), (64, 51), (64, 52), (64, 53), (64, 54), (64, 55), (64, 56), (64, 57), (64, 58), (64, 59), (64, 60), (64, 61), (64, 62), (64, 63), (63, 37), (63, 38), (63, 39), (63, 40), (63, 41), (63, 42), (63, 43), (63, 44), (63, 45), (63, 46), (63, 47), (63, 48), (63, 49), (63, 50), (63, 51), (63, 52), (63, 53), (63, 54), (63, 55), (63, 56), (63, 57), (63, 58), (63, 59), (63, 60), (63, 61), (63, 62), (62, 38), (62, 39), (62, 40), (62, 41), (62, 42), (62, 43), (62, 44), (62, 45), (62, 46), (62, 47), (62, 48), (62, 49), (62, 50), (62, 51), (62, 52), (62, 53), (62, 54), (62, 55), (62, 56), (62, 57), (62, 58), (62, 59), (62, 60), (62, 61), (61, 39), (61, 40), (61, 41), (61, 42), (61, 43), (61, 44), (61, 45), (61, 46), (61, 47), (61, 48), (61, 49), (61, 50), (61, 51), (61, 52), (61, 53), (61, 54), (61, 55), (61, 56), (61, 57), (61, 58), (61, 59), (61, 60), (60, 40), (60, 41), (60, 42), (60, 43), (60, 44), (60, 45), (60, 46), (60, 47), (60, 48), (60, 49), (60, 50), (60, 51), (60, 52), (60, 53), (60, 54), (60, 55), (60, 56), (60, 57), (60, 58), (60, 59), (59, 41), (59, 42), (59, 43), (59, 44), (59, 45), (59, 46), (59, 47), (59, 48), (59, 49), (59, 50), (59, 51), (59, 52), (59, 53), (59, 54), (59, 55), (59, 56), (59, 57), (59, 58), (58, 42), (58, 43), (58, 44), (58, 45), (58, 46), (58, 47), (58, 48), (58, 49), (58, 50), (58, 51), (58, 52), (58, 53), (58, 54), (58, 55), (58, 56), (58, 57), (57, 43), (57, 44), (57, 45), (57, 46), (57, 47), (57, 48), (57, 49), (57, 50), (57, 51), (57, 52), (57, 53), (57, 54), (57, 55), (57, 56), (56, 44), (56, 45), (56, 46), (56, 47), (56, 48), (56, 49), (56, 50), (56, 51), (56, 52), (56, 53), (56, 54), (56, 55), (55, 45), (55, 46), (55, 47), (55, 48), (55, 49), (55, 50), (55, 51), (55, 52), (55, 53), (55, 54), (54, 46), (54, 47), (54, 48), (54, 49), (54, 50), (54, 51), (54, 52), (54, 53), (53, 47), (53, 48), (53, 49), (53, 50), (53, 51), (53, 52), (52, 48), (52, 49), (52, 50), (52, 51), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10), (0, 11), (0, 12), (0, 13), (0, 14), (0, 15), (0, 16), (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (0, 22), (0, 23), (0, 24), (0, 25), (0, 26), (0, 27), (0, 28), (0, 29), (0, 30), (0, 31), (0, 32), (0, 33), (0, 34), (0, 35), (0, 36), (0, 37), (0, 38), (0, 39), (0, 40), (0, 41), (0, 42), (0, 43), (0, 44), (0, 45), (0, 46), (0, 47), (0, 48), (0, 49), (0, 50), (0, 51), (0, 52), (0, 53), (0, 54), (0, 55), (0, 56), (0, 57), (0, 58), (0, 59), (0, 60), (0, 61), (0, 62), (0, 63), (0, 64), (0, 65), (0, 66), (0, 67), (0, 68), (0, 69), (0, 70), (0, 71), (0, 72), (0, 73), (0, 74), (0, 75), (0, 76), (0, 77), (0, 78), (0, 79), (0, 80), (0, 81), (0, 82), (0, 83), (0, 84), (0, 85), (0, 86), (0, 87), (0, 88), (0, 89), (0, 90), (0, 91), (0, 92), (0, 93), (0, 94), (0, 95), (0, 96), (0, 97), (0, 98), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20), (1, 21), (1, 22), (1, 23), (1, 24), (1, 25), (1, 26), (1, 27), (1, 28), (1, 29), (1, 30), (1, 31), (1, 32), (1, 33), (1, 34), (1, 35), (1, 36), (1, 37), (1, 38), (1, 39), (1, 40), (1, 41), (1, 42), (1, 43), (1, 44), (1, 45), (1, 46), (1, 47), (1, 48), (1, 49), (1, 50), (1, 51), (1, 52), (1, 53), (1, 54), (1, 55), (1, 56), (1, 57), (1, 58), (1, 59), (1, 60), (1, 61), (1, 62), (1, 63), (1, 64), (1, 65), (1, 66), (1, 67), (1, 68), (1, 69), (1, 70), (1, 71), (1, 72), (1, 73), (1, 74), (1, 75), (1, 76), (1, 77), (1, 78), (1, 79), (1, 80), (1, 81), (1, 82), (1, 83), (1, 84), (1, 85), (1, 86), (1, 87), (1, 88), (1, 89), (1, 90), (1, 91), (1, 92), (1, 93), (1, 94), (1, 95), (1, 96), (1, 97), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (2, 10), (2, 11), (2, 12), (2, 13), (2, 14), (2, 15), (2, 16), (2, 17), (2, 18), (2, 19), (2, 20), (2, 21), (2, 22), (2, 23), (2, 24), (2, 25), (2, 26), (2, 27), (2, 28), (2, 29), (2, 30), (2, 31), (2, 32), (2, 33), (2, 34), (2, 35), (2, 36), (2, 37), (2, 38), (2, 39), (2, 40), (2, 41), (2, 42), (2, 43), (2, 44), (2, 45), (2, 46), (2, 47), (2, 48), (2, 49), (2, 50), (2, 51), (2, 52), (2, 53), (2, 54), (2, 55), (2, 56), (2, 57), (2, 58), (2, 59), (2, 60), (2, 61), (2, 62), (2, 63), (2, 64), (2, 65), (2, 66), (2, 67), (2, 68), (2, 69), (2, 70), (2, 71), (2, 72), (2, 73), (2, 74), (2, 75), (2, 76), (2, 77), (2, 78), (2, 79), (2, 80), (2, 81), (2, 82), (2, 83), (2, 84), (2, 85), (2, 86), (2, 87), (2, 88), (2, 89), (2, 90), (2, 91), (2, 92), (2, 93), (2, 94), (2, 95), (2, 96), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8), (3, 9), (3, 10), (3, 11), (3, 12), (3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (3, 18), (3, 19), (3, 20), (3, 21), (3, 22), (3, 23), (3, 24), (3, 25), (3, 26), (3, 27), (3, 28), (3, 29), (3, 30), (3, 31), (3, 32), (3, 33), (3, 34), (3, 35), (3, 36), (3, 37), (3, 38), (3, 39), (3, 40), (3, 41), (3, 42), (3, 43), (3, 44), (3, 45), (3, 46), (3, 47), (3, 48), (3, 49), (3, 50), (3, 51), (3, 52), (3, 53), (3, 54), (3, 55), (3, 56), (3, 57), (3, 58), (3, 59), (3, 60), (3, 61), (3, 62), (3, 63), (3, 64), (3, 65), (3, 66), (3, 67), (3, 68), (3, 69), (3, 70), (3, 71), (3, 72), (3, 73), (3, 74), (3, 75), (3, 76), (3, 77), (3, 78), (3, 79), (3, 80), (3, 81), (3, 82), (3, 83), (3, 84), (3, 85), (3, 86), (3, 87), (3, 88), (3, 89), (3, 90), (3, 91), (3, 92), (3, 93), (3, 94), (3, 95), (4, 5), (4, 6), (4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12), (4, 13), (4, 14), (4, 15), (4, 16), (4, 17), (4, 18), (4, 19), (4, 20), (4, 21), (4, 22), (4, 23), (4, 24), (4, 25), (4, 26), (4, 27), (4, 28), (4, 29), (4, 30), (4, 31), (4, 32), (4, 33), (4, 34), (4, 35), (4, 36), (4, 37), (4, 38), (4, 39), (4, 40), (4, 41), (4, 42), (4, 43), (4, 44), (4, 45), (4, 46), (4, 47), (4, 48), (4, 49), (4, 50), (4, 51), (4, 52), (4, 53), (4, 54), (4, 55), (4, 56), (4, 57), (4, 58), (4, 59), (4, 60), (4, 61), (4, 62), (4, 63), (4, 64), (4, 65), (4, 66), (4, 67), (4, 68), (4, 69), (4, 70), (4, 71), (4, 72), (4, 73), (4, 74), (4, 75), (4, 76), (4, 77), (4, 78), (4, 79), (4, 80), (4, 81), (4, 82), (4, 83), (4, 84), (4, 85), (4, 86), (4, 87), (4, 88), (4, 89), (4, 90), (4, 91), (4, 92), (4, 93), (4, 94), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10), (5, 11), (5, 12), (5, 13), (5, 14), (5, 15), (5, 16), (5, 17), (5, 18), (5, 19), (5, 20), (5, 21), (5, 22), (5, 23), (5, 24), (5, 25), (5, 26), (5, 27), (5, 28), (5, 29), (5, 30), (5, 31), (5, 32), (5, 33), (5, 34), (5, 35), (5, 36), (5, 37), (5, 38), (5, 39), (5, 40), (5, 41), (5, 42), (5, 43), (5, 44), (5, 45), (5, 46), (5, 47), (5, 48), (5, 49), (5, 50), (5, 51), (5, 52), (5, 53), (5, 54), (5, 55), (5, 56), (5, 57), (5, 58), (5, 59), (5, 60), (5, 61), (5, 62), (5, 63), (5, 64), (5, 65), (5, 66), (5, 67), (5, 68), (5, 69), (5, 70), (5, 71), (5, 72), (5, 73), (5, 74), (5, 75), (5, 76), (5, 77), (5, 78), (5, 79), (5, 80), (5, 81), (5, 82), (5, 83), (5, 84), (5, 85), (5, 86), (5, 87), (5, 88), (5, 89), (5, 90), (5, 91), (5, 92), (5, 93), (6, 7), (6, 8), (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14), (6, 15), (6, 16), (6, 17), (6, 18), (6, 19), (6, 20), (6, 21), (6, 22), (6, 23), (6, 24), (6, 25), (6, 26), (6, 27), (6, 28), (6, 29), (6, 30), (6, 31), (6, 32), (6, 33), (6, 34), (6, 35), (6, 36), (6, 37), (6, 38), (6, 39), (6, 40), (6, 41), (6, 42), (6, 43), (6, 44), (6, 45), (6, 46), (6, 47), (6, 48), (6, 49), (6, 50), (6, 51), (6, 52), (6, 53), (6, 54), (6, 55), (6, 56), (6, 57), (6, 58), (6, 59), (6, 60), (6, 61), (6, 62), (6, 63), (6, 64), (6, 65), (6, 66), (6, 67), (6, 68), (6, 69), (6, 70), (6, 71), (6, 72), (6, 73), (6, 74), (6, 75), (6, 76), (6, 77), (6, 78), (6, 79), (6, 80), (6, 81), (6, 82), (6, 83), (6, 84), (6, 85), (6, 86), (6, 87), (6, 88), (6, 89), (6, 90), (6, 91), (6, 92), (7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20), (7, 21), (7, 22), (7, 23), (7, 24), (7, 25), (7, 26), (7, 27), (7, 28), (7, 29), (7, 30), (7, 31), (7, 32), (7, 33), (7, 34), (7, 35), (7, 36), (7, 37), (7, 38), (7, 39), (7, 40), (7, 41), (7, 42), (7, 43), (7, 44), (7, 45), (7, 46), (7, 47), (7, 48), (7, 49), (7, 50), (7, 51), (7, 52), (7, 53), (7, 54), (7, 55), (7, 56), (7, 57), (7, 58), (7, 59), (7, 60), (7, 61), (7, 62), (7, 63), (7, 64), (7, 65), (7, 66), (7, 67), (7, 68), (7, 69), (7, 70), (7, 71), (7, 72), (7, 73), (7, 74), (7, 75), (7, 76), (7, 77), (7, 78), (7, 79), (7, 80), (7, 81), (7, 82), (7, 83), (7, 84), (7, 85), (7, 86), (7, 87), (7, 88), (7, 89), (7, 90), (7, 91), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13), (8, 14), (8, 15), (8, 16), (8, 17), (8, 18), (8, 19), (8, 20), (8, 21), (8, 22), (8, 23), (8, 24), (8, 25), (8, 26), (8, 27), (8, 28), (8, 29), (8, 30), (8, 31), (8, 32), (8, 33), (8, 34), (8, 35), (8, 36), (8, 37), (8, 38), (8, 39), (8, 40), (8, 41), (8, 42), (8, 43), (8, 44), (8, 45), (8, 46), (8, 47), (8, 48), (8, 49), (8, 50), (8, 51), (8, 52), (8, 53), (8, 54), (8, 55), (8, 56), (8, 57), (8, 58), (8, 59), (8, 60), (8, 61), (8, 62), (8, 63), (8, 64), (8, 65), (8, 66), (8, 67), (8, 68), (8, 69), (8, 70), (8, 71), (8, 72), (8, 73), (8, 74), (8, 75), (8, 76), (8, 77), (8, 78), (8, 79), (8, 80), (8, 81), (8, 82), (8, 83), (8, 84), (8, 85), (8, 86), (8, 87), (8, 88), (8, 89), (8, 90), (9, 10), (9, 11), (9, 12), (9, 13), (9, 14), (9, 15), (9, 16), (9, 17), (9, 18), (9, 19), (9, 20), (9, 21), (9, 22), (9, 23), (9, 24), (9, 25), (9, 26), (9, 27), (9, 28), (9, 29), (9, 30), (9, 31), (9, 32), (9, 33), (9, 34), (9, 35), (9, 36), (9, 37), (9, 38), (9, 39), (9, 40), (9, 41), (9, 42), (9, 43), (9, 44), (9, 45), (9, 46), (9, 47), (9, 48), (9, 49), (9, 50), (9, 51), (9, 52), (9, 53), (9, 54), (9, 55), (9, 56), (9, 57), (9, 58), (9, 59), (9, 60), (9, 61), (9, 62), (9, 63), (9, 64), (9, 65), (9, 66), (9, 67), (9, 68), (9, 69), (9, 70), (9, 71), (9, 72), (9, 73), (9, 74), (9, 75), (9, 76), (9, 77), (9, 78), (9, 79), (9, 80), (9, 81), (9, 82), (9, 83), (9, 84), (9, 85), (9, 86), (9, 87), (9, 88), (9, 89), (10, 11), (10, 12), (10, 13), (10, 14), (10, 15), (10, 16), (10, 17), (10, 18), (10, 19), (10, 20), (10, 21), (10, 22), (10, 23), (10, 24), (10, 25), (10, 26), (10, 27), (10, 28), (10, 29), (10, 30), (10, 31), (10, 32), (10, 33), (10, 34), (10, 35), (10, 36), (10, 37), (10, 38), (10, 39), (10, 40), (10, 41), (10, 42), (10, 43), (10, 44), (10, 45), (10, 46), (10, 47), (10, 48), (10, 49), (10, 50), (10, 51), (10, 52), (10, 53), (10, 54), (10, 55), (10, 56), (10, 57), (10, 58), (10, 59), (10, 60), (10, 61), (10, 62), (10, 63), (10, 64), (10, 65), (10, 66), (10, 67), (10, 68), (10, 69), (10, 70), (10, 71), (10, 72), (10, 73), (10, 74), (10, 75), (10, 76), (10, 77), (10, 78), (10, 79), (10, 80), (10, 81), (10, 82), (10, 83), (10, 84), (10, 85), (10, 86), (10, 87), (10, 88), (11, 12), (11, 13), (11, 14), (11, 15), (11, 16), (11, 17), (11, 18), (11, 19), (11, 20), (11, 21), (11, 22), (11, 23), (11, 24), (11, 25), (11, 26), (11, 27), (11, 28), (11, 29), (11, 30), (11, 31), (11, 32), (11, 33), (11, 34), (11, 35), (11, 36), (11, 37), (11, 38), (11, 39), (11, 40), (11, 41), (11, 42), (11, 43), (11, 44), (11, 45), (11, 46), (11, 47), (11, 48), (11, 49), (11, 50), (11, 51), (11, 52), (11, 53), (11, 54), (11, 55), (11, 56), (11, 57), (11, 58), (11, 59), (11, 60), (11, 61), (11, 62), (11, 63), (11, 64), (11, 65), (11, 66), (11, 67), (11, 68), (11, 69), (11, 70), (11, 71), (11, 72), (11, 73), (11, 74), (11, 75), (11, 76), (11, 77), (11, 78), (11, 79), (11, 80), (11, 81), (11, 82), (11, 83), (11, 84), (11, 85), (11, 86), (11, 87), (12, 13), (12, 14), (12, 15), (12, 16), (12, 17), (12, 18), (12, 19), (12, 20), (12, 21), (12, 22), (12, 23), (12, 24), (12, 25), (12, 26), (12, 27), (12, 28), (12, 29), (12, 30), (12, 31), (12, 32), (12, 33), (12, 34), (12, 35), (12, 36), (12, 37), (12, 38), (12, 39), (12, 40), (12, 41), (12, 42), (12, 43), (12, 44), (12, 45), (12, 46), (12, 47), (12, 48), (12, 49), (12, 50), (12, 51), (12, 52), (12, 53), (12, 54), (12, 55), (12, 56), (12, 57), (12, 58), (12, 59), (12, 60), (12, 61), (12, 62), (12, 63), (12, 64), (12, 65), (12, 66), (12, 67), (12, 68), (12, 69), (12, 70), (12, 71), (12, 72), (12, 73), (12, 74), (12, 75), (12, 76), (12, 77), (12, 78), (12, 79), (12, 80), (12, 81), (12, 82), (12, 83), (12, 84), (12, 85), (12, 86), (13, 14), (13, 15), (13, 16), (13, 17), (13, 18), (13, 19), (13, 20), (13, 21), (13, 22), (13, 23), (13, 24), (13, 25), (13, 26), (13, 27), (13, 28), (13, 29), (13, 30), (13, 31), (13, 32), (13, 33), (13, 34), (13, 35), (13, 36), (13, 37), (13, 38), (13, 39), (13, 40), (13, 41), (13, 42), (13, 43), (13, 44), (13, 45), (13, 46), (13, 47), (13, 48), (13, 49), (13, 50), (13, 51), (13, 52), (13, 53), (13, 54), (13, 55), (13, 56), (13, 57), (13, 58), (13, 59), (13, 60), (13, 61), (13, 62), (13, 63), (13, 64), (13, 65), (13, 66), (13, 67), (13, 68), (13, 69), (13, 70), (13, 71), (13, 72), (13, 73), (13, 74), (13, 75), (13, 76), (13, 77), (13, 78), (13, 79), (13, 80), (13, 81), (13, 82), (13, 83), (13, 84), (13, 85), (14, 15), (14, 16), (14, 17), (14, 18), (14, 19), (14, 20), (14, 21), (14, 22), (14, 23), (14, 24), (14, 25), (14, 26), (14, 27), (14, 28), (14, 29), (14, 30), (14, 31), (14, 32), (14, 33), (14, 34), (14, 35), (14, 36), (14, 37), (14, 38), (14, 39), (14, 40), (14, 41), (14, 42), (14, 43), (14, 44), (14, 45), (14, 46), (14, 47), (14, 48), (14, 49), (14, 50), (14, 51), (14, 52), (14, 53), (14, 54), (14, 55), (14, 56), (14, 57), (14, 58), (14, 59), (14, 60), (14, 61), (14, 62), (14, 63), (14, 64), (14, 65), (14, 66), (14, 67), (14, 68), (14, 69), (14, 70), (14, 71), (14, 72), (14, 73), (14, 74), (14, 75), (14, 76), (14, 77), (14, 78), (14, 79), (14, 80), (14, 81), (14, 82), (14, 83), (14, 84), (15, 16), (15, 17), (15, 18), (15, 19), (15, 20), (15, 21), (15, 22), (15, 23), (15, 24), (15, 25), (15, 26), (15, 27), (15, 28), (15, 29), (15, 30), (15, 31), (15, 32), (15, 33), (15, 34), (15, 35), (15, 36), (15, 37), (15, 38), (15, 39), (15, 40), (15, 41), (15, 42), (15, 43), (15, 44), (15, 45), (15, 46), (15, 47), (15, 48), (15, 49), (15, 50), (15, 51), (15, 52), (15, 53), (15, 54), (15, 55), (15, 56), (15, 57), (15, 58), (15, 59), (15, 60), (15, 61), (15, 62), (15, 63), (15, 64), (15, 65), (15, 66), (15, 67), (15, 68), (15, 69), (15, 70), (15, 71), (15, 72), (15, 73), (15, 74), (15, 75), (15, 76), (15, 77), (15, 78), (15, 79), (15, 80), (15, 81), (15, 82), (15, 83), (16, 17), (16, 18), (16, 19), (16, 20), (16, 21), (16, 22), (16, 23), (16, 24), (16, 25), (16, 26), (16, 27), (16, 28), (16, 29), (16, 30), (16, 31), (16, 32), (16, 33), (16, 34), (16, 35), (16, 36), (16, 37), (16, 38), (16, 39), (16, 40), (16, 41), (16, 42), (16, 43), (16, 44), (16, 45), (16, 46), (16, 47), (16, 48), (16, 49), (16, 50), (16, 51), (16, 52), (16, 53), (16, 54), (16, 55), (16, 56), (16, 57), (16, 58), (16, 59), (16, 60), (16, 61), (16, 62), (16, 63), (16, 64), (16, 65), (16, 66), (16, 67), (16, 68), (16, 69), (16, 70), (16, 71), (16, 72), (16, 73), (16, 74), (16, 75), (16, 76), (16, 77), (16, 78), (16, 79), (16, 80), (16, 81), (16, 82), (17, 18), (17, 19), (17, 20), (17, 21), (17, 22), (17, 23), (17, 24), (17, 25), (17, 26), (17, 27), (17, 28), (17, 29), (17, 30), (17, 31), (17, 32), (17, 33), (17, 34), (17, 35), (17, 36), (17, 37), (17, 38), (17, 39), (17, 40), (17, 41), (17, 42), (17, 43), (17, 44), (17, 45), (17, 46), (17, 47), (17, 48), (17, 49), (17, 50), (17, 51), (17, 52), (17, 53), (17, 54), (17, 55), (17, 56), (17, 57), (17, 58), (17, 59), (17, 60), (17, 61), (17, 62), (17, 63), (17, 64), (17, 65), (17, 66), (17, 67), (17, 68), (17, 69), (17, 70), (17, 71), (17, 72), (17, 73), (17, 74), (17, 75), (17, 76), (17, 77), (17, 78), (17, 79), (17, 80), (17, 81), (18, 19), (18, 20), (18, 21), (18, 22), (18, 23), (18, 24), (18, 25), (18, 26), (18, 27), (18, 28), (18, 29), (18, 30), (18, 31), (18, 32), (18, 33), (18, 34), (18, 35), (18, 36), (18, 37), (18, 38), (18, 39), (18, 40), (18, 41), (18, 42), (18, 43), (18, 44), (18, 45), (18, 46), (18, 47), (18, 48), (18, 49), (18, 50), (18, 51), (18, 52), (18, 53), (18, 54), (18, 55), (18, 56), (18, 57), (18, 58), (18, 59), (18, 60), (18, 61), (18, 62), (18, 63), (18, 64), (18, 65), (18, 66), (18, 67), (18, 68), (18, 69), (18, 70), (18, 71), (18, 72), (18, 73), (18, 74), (18, 75), (18, 76), (18, 77), (18, 78), (18, 79), (18, 80), (19, 20), (19, 21), (19, 22), (19, 23), (19, 24), (19, 25), (19, 26), (19, 27), (19, 28), (19, 29), (19, 30), (19, 31), (19, 32), (19, 33), (19, 34), (19, 35), (19, 36), (19, 37), (19, 38), (19, 39), (19, 40), (19, 41), (19, 42), (19, 43), (19, 44), (19, 45), (19, 46), (19, 47), (19, 48), (19, 49), (19, 50), (19, 51), (19, 52), (19, 53), (19, 54), (19, 55), (19, 56), (19, 57), (19, 58), (19, 59), (19, 60), (19, 61), (19, 62), (19, 63), (19, 64), (19, 65), (19, 66), (19, 67), (19, 68), (19, 69), (19, 70), (19, 71), (19, 72), (19, 73), (19, 74), (19, 75), (19, 76), (19, 77), (19, 78), (19, 79), (20, 21), (20, 22), (20, 23), (20, 24), (20, 25), (20, 26), (20, 27), (20, 28), (20, 29), (20, 30), (20, 31), (20, 32), (20, 33), (20, 34), (20, 35), (20, 36), (20, 37), (20, 38), (20, 39), (20, 40), (20, 41), (20, 42), (20, 43), (20, 44), (20, 45), (20, 46), (20, 47), (20, 48), (20, 49), (20, 50), (20, 51), (20, 52), (20, 53), (20, 54), (20, 55), (20, 56), (20, 57), (20, 58), (20, 59), (20, 60), (20, 61), (20, 62), (20, 63), (20, 64), (20, 65), (20, 66), (20, 67), (20, 68), (20, 69), (20, 70), (20, 71), (20, 72), (20, 73), (20, 74), (20, 75), (20, 76), (20, 77), (20, 78), (21, 22), (21, 23), (21, 24), (21, 25), (21, 26), (21, 27), (21, 28), (21, 29), (21, 30), (21, 31), (21, 32), (21, 33), (21, 34), (21, 35), (21, 36), (21, 37), (21, 38), (21, 39), (21, 40), (21, 41), (21, 42), (21, 43), (21, 44), (21, 45), (21, 46), (21, 47), (21, 48), (21, 49), (21, 50), (21, 51), (21, 52), (21, 53), (21, 54), (21, 55), (21, 56), (21, 57), (21, 58), (21, 59), (21, 60), (21, 61), (21, 62), (21, 63), (21, 64), (21, 65), (21, 66), (21, 67), (21, 68), (21, 69), (21, 70), (21, 71), (21, 72), (21, 73), (21, 74), (21, 75), (21, 76), (21, 77), (22, 23), (22, 24), (22, 25), (22, 26), (22, 27), (22, 28), (22, 29), (22, 30), (22, 31), (22, 32), (22, 33), (22, 34), (22, 35), (22, 36), (22, 37), (22, 38), (22, 39), (22, 40), (22, 41), (22, 42), (22, 43), (22, 44), (22, 45), (22, 46), (22, 47), (22, 48), (22, 49), (22, 50), (22, 51), (22, 52), (22, 53), (22, 54), (22, 55), (22, 56), (22, 57), (22, 58), (22, 59), (22, 60), (22, 61), (22, 62), (22, 63), (22, 64), (22, 65), (22, 66), (22, 67), (22, 68), (22, 69), (22, 70), (22, 71), (22, 72), (22, 73), (22, 74), (22, 75), (22, 76), (23, 24), (23, 25), (23, 26), (23, 27), (23, 28), (23, 29), (23, 30), (23, 31), (23, 32), (23, 33), (23, 34), (23, 35), (23, 36), (23, 37), (23, 38), (23, 39), (23, 40), (23, 41), (23, 42), (23, 43), (23, 44), (23, 45), (23, 46), (23, 47), (23, 48), (23, 49), (23, 50), (23, 51), (23, 52), (23, 53), (23, 54), (23, 55), (23, 56), (23, 57), (23, 58), (23, 59), (23, 60), (23, 61), (23, 62), (23, 63), (23, 64), (23, 65), (23, 66), (23, 67), (23, 68), (23, 69), (23, 70), (23, 71), (23, 72), (23, 73), (23, 74), (23, 75), (24, 25), (24, 26), (24, 27), (24, 28), (24, 29), (24, 30), (24, 31), (24, 32), (24, 33), (24, 34), (24, 35), (24, 36), (24, 37), (24, 38), (24, 39), (24, 40), (24, 41), (24, 42), (24, 43), (24, 44), (24, 45), (24, 46), (24, 47), (24, 48), (24, 49), (24, 50), (24, 51), (24, 52), (24, 53), (24, 54), (24, 55), (24, 56), (24, 57), (24, 58), (24, 59), (24, 60), (24, 61), (24, 62), (24, 63), (24, 64), (24, 65), (24, 66), (24, 67), (24, 68), (24, 69), (24, 70), (24, 71), (24, 72), (24, 73), (24, 74), (25, 26), (25, 27), (25, 28), (25, 29), (25, 30), (25, 31), (25, 32), (25, 33), (25, 34), (25, 35), (25, 36), (25, 37), (25, 38), (25, 39), (25, 40), (25, 41), (25, 42), (25, 43), (25, 44), (25, 45), (25, 46), (25, 47), (25, 48), (25, 49), (25, 50), (25, 51), (25, 52), (25, 53), (25, 54), (25, 55), (25, 56), (25, 57), (25, 58), (25, 59), (25, 60), (25, 61), (25, 62), (25, 63), (25, 64), (25, 65), (25, 66), (25, 67), (25, 68), (25, 69), (25, 70), (25, 71), (25, 72), (25, 73), (26, 27), (26, 28), (26, 29), (26, 30), (26, 31), (26, 32), (26, 33), (26, 34), (26, 35), (26, 36), (26, 37), (26, 38), (26, 39), (26, 40), (26, 41), (26, 42), (26, 43), (26, 44), (26, 45), (26, 46), (26, 47), (26, 48), (26, 49), (26, 50), (26, 51), (26, 52), (26, 53), (26, 54), (26, 55), (26, 56), (26, 57), (26, 58), (26, 59), (26, 60), (26, 61), (26, 62), (26, 63), (26, 64), (26, 65), (26, 66), (26, 67), (26, 68), (26, 69), (26, 70), (26, 71), (26, 72), (27, 28), (27, 29), (27, 30), (27, 31), (27, 32), (27, 33), (27, 34), (27, 35), (27, 36), (27, 37), (27, 38), (27, 39), (27, 40), (27, 41), (27, 42), (27, 43), (27, 44), (27, 45), (27, 46), (27, 47), (27, 48), (27, 49), (27, 50), (27, 51), (27, 52), (27, 53), (27, 54), (27, 55), (27, 56), (27, 57), (27, 58), (27, 59), (27, 60), (27, 61), (27, 62), (27, 63), (27, 64), (27, 65), (27, 66), (27, 67), (27, 68), (27, 69), (27, 70), (27, 71), (28, 29), (28, 30), (28, 31), (28, 32), (28, 33), (28, 34), (28, 35), (28, 36), (28, 37), (28, 38), (28, 39), (28, 40), (28, 41), (28, 42), (28, 43), (28, 44), (28, 45), (28, 46), (28, 47), (28, 48), (28, 49), (28, 50), (28, 51), (28, 52), (28, 53), (28, 54), (28, 55), (28, 56), (28, 57), (28, 58), (28, 59), (28, 60), (28, 61), (28, 62), (28, 63), (28, 64), (28, 65), (28, 66), (28, 67), (28, 68), (28, 69), (28, 70), (29, 30), (29, 31), (29, 32), (29, 33), (29, 34), (29, 35), (29, 36), (29, 37), (29, 38), (29, 39), (29, 40), (29, 41), (29, 42), (29, 43), (29, 44), (29, 45), (29, 46), (29, 47), (29, 48), (29, 49), (29, 50), (29, 51), (29, 52), (29, 53), (29, 54), (29, 55), (29, 56), (29, 57), (29, 58), (29, 59), (29, 60), (29, 61), (29, 62), (29, 63), (29, 64), (29, 65), (29, 66), (29, 67), (29, 68), (29, 69), (30, 31), (30, 32), (30, 33), (30, 34), (30, 35), (30, 36), (30, 37), (30, 38), (30, 39), (30, 40), (30, 41), (30, 42), (30, 43), (30, 44), (30, 45), (30, 46), (30, 47), (30, 48), (30, 49), (30, 50), (30, 51), (30, 52), (30, 53), (30, 54), (30, 55), (30, 56), (30, 57), (30, 58), (30, 59), (30, 60), (30, 61), (30, 62), (30, 63), (30, 64), (30, 65), (30, 66), (30, 67), (30, 68), (31, 32), (31, 33), (31, 34), (31, 35), (31, 36), (31, 37), (31, 38), (31, 39), (31, 40), (31, 41), (31, 42), (31, 43), (31, 44), (31, 45), (31, 46), (31, 47), (31, 48), (31, 49), (31, 50), (31, 51), (31, 52), (31, 53), (31, 54), (31, 55), (31, 56), (31, 57), (31, 58), (31, 59), (31, 60), (31, 61), (31, 62), (31, 63), (31, 64), (31, 65), (31, 66), (31, 67), (32, 33), (32, 34), (32, 35), (32, 36), (32, 37), (32, 38), (32, 39), (32, 40), (32, 41), (32, 42), (32, 43), (32, 44), (32, 45), (32, 46), (32, 47), (32, 48), (32, 49), (32, 50), (32, 51), (32, 52), (32, 53), (32, 54), (32, 55), (32, 56), (32, 57), (32, 58), (32, 59), (32, 60), (32, 61), (32, 62), (32, 63), (32, 64), (32, 65), (32, 66), (33, 34), (33, 35), (33, 36), (33, 37), (33, 38), (33, 39), (33, 40), (33, 41), (33, 42), (33, 43), (33, 44), (33, 45), (33, 46), (33, 47), (33, 48), (33, 49), (33, 50), (33, 51), (33, 52), (33, 53), (33, 54), (33, 55), (33, 56), (33, 57), (33, 58), (33, 59), (33, 60), (33, 61), (33, 62), (33, 63), (33, 64), (33, 65), (34, 35), (34, 36), (34, 37), (34, 38), (34, 39), (34, 40), (34, 41), (34, 42), (34, 43), (34, 44), (34, 45), (34, 46), (34, 47), (34, 48), (34, 49), (34, 50), (34, 51), (34, 52), (34, 53), (34, 54), (34, 55), (34, 56), (34, 57), (34, 58), (34, 59), (34, 60), (34, 61), (34, 62), (34, 63), (34, 64), (35, 36), (35, 37), (35, 38), (35, 39), (35, 40), (35, 41), (35, 42), (35, 43), (35, 44), (35, 45), (35, 46), (35, 47), (35, 48), (35, 49), (35, 50), (35, 51), (35, 52), (35, 53), (35, 54), (35, 55), (35, 56), (35, 57), (35, 58), (35, 59), (35, 60), (35, 61), (35, 62), (35, 63), (36, 37), (36, 38), (36, 39), (36, 40), (36, 41), (36, 42), (36, 43), (36, 44), (36, 45), (36, 46), (36, 47), (36, 48), (36, 49), (36, 50), (36, 51), (36, 52), (36, 53), (36, 54), (36, 55), (36, 56), (36, 57), (36, 58), (36, 59), (36, 60), (36, 61), (36, 62), (37, 38), (37, 39), (37, 40), (37, 41), (37, 42), (37, 43), (37, 44), (37, 45), (37, 46), (37, 47), (37, 48), (37, 49), (37, 50), (37, 51), (37, 52), (37, 53), (37, 54), (37, 55), (37, 56), (37, 57), (37, 58), (37, 59), (37, 60), (37, 61), (38, 39), (38, 40), (38, 41), (38, 42), (38, 43), (38, 44), (38, 45), (38, 46), (38, 47), (38, 48), (38, 49), (38, 50), (38, 51), (38, 52), (38, 53), (38, 54), (38, 55), (38, 56), (38, 57), (38, 58), (38, 59), (38, 60), (39, 40), (39, 41), (39, 42), (39, 43), (39, 44), (39, 45), (39, 46), (39, 47), (39, 48), (39, 49), (39, 50), (39, 51), (39, 52), (39, 53), (39, 54), (39, 55), (39, 56), (39, 57), (39, 58), (39, 59), (40, 41), (40, 42), (40, 43), (40, 44), (40, 45), (40, 46), (40, 47), (40, 48), (40, 49), (40, 50), (40, 51), (40, 52), (40, 53), (40, 54), (40, 55), (40, 56), (40, 57), (40, 58), (41, 42), (41, 43), (41, 44), (41, 45), (41, 46), (41, 47), (41, 48), (41, 49), (41, 50), (41, 51), (41, 52), (41, 53), (41, 54), (41, 55), (41, 56), (41, 57), (42, 43), (42, 44), (42, 45), (42, 46), (42, 47), (42, 48), (42, 49), (42, 50), (42, 51), (42, 52), (42, 53), (42, 54), (42, 55), (42, 56), (43, 44), (43, 45), (43, 46), (43, 47), (43, 48), (43, 49), (43, 50), (43, 51), (43, 52), (43, 53), (43, 54), (43, 55), (44, 45), (44, 46), (44, 47), (44, 48), (44, 49), (44, 50), (44, 51), (44, 52), (44, 53), (44, 54), (45, 46), (45, 47), (45, 48), (45, 49), (45, 50), (45, 51), (45, 52), (45, 53), (46, 47), (46, 48), (46, 49), (46, 50), (46, 51), (46, 52), (47, 48), (47, 49), (47, 50), (47, 51), (48, 49), (48, 50)]

    def get_next_formation_points(self, state):
        return self.all_points
    
    def get_phase(self, phase, state, retract, movable):
        return 0

class QuadraticFormationEnhanced(Formation):
    def __init__(self):
        self.all_points = self.get_quadrants_formation()

    def get_next_formation_points(self, state):
        return self.all_points
    
    def get_phase(self, phase, state, retract, movable):
        return 0

    def get_quadrants_formation(self):
        precomputed_quadrants = [
            *self.top_quadrant(),
            *self.bottom_quadrant(),
            *self.right_quadrant(),
            *self.left_quadrant()]
        return precomputed_quadrants

    def top_quadrant(self):
        """
            Goal: Precomputation 
            1. define a top arc between 135deg and 45 deg
        """
        quadratic_formation = list()
        x, y = (50,50)
        while (0,0) not in quadratic_formation:
            quadratic_formation.append((x, y))
            quadratic_formation.append((x - 1, y))
            x, y = (x - 1, y - 1)
        quadratic_formation.remove((-1, 0)) # removes (0, -1)
        x, y = (51, 50)

        while (99, 1) not in quadratic_formation:
            quadratic_formation.append((x, y))
            quadratic_formation.append((x, y - 1))
            x, y = (x + 1, y - 1)
            print((x, y))
        quadratic_formation.append((99, 0))

        start_col = 2
        end_col = 98
        for row in range(0, 50, 8):
            for col in range(start_col, end_col):
                quadratic_formation.append((col, row))
            start_col += 1
            end_col -= 1

        return quadratic_formation

    def bottom_quadrant(self):
        """
            Goal: Precomputation 
            2. define a second arc and sweep from 225deg to 315 deg
        """
        quadratic_formation = list()
        x, y = (49, 51)
        while (0,99) not in quadratic_formation:
            quadratic_formation.append((x, y))
            quadratic_formation.append((x - 1, y))
            x, y = (x - 1, y + 1)

        x, y = (51, 51)

        while (99, 99) not in quadratic_formation:
            quadratic_formation.append((x, y))
            quadratic_formation.append((x + 1, y))
            x, y = (x + 1, y + 1)

        quadratic_formation.pop(-1)

        # filling row from left to right
        col = 1
        for row in range(99, 50, -8):
            col += 1
            for i in range(col, 100 - col + 1):
                if (i, row) not in quadratic_formation:
                    quadratic_formation.append((i, row))
                else:
                    break

        return quadratic_formation

    def right_quadrant(self):
        """
            Goal: Precomputation 
            3. define a third arc and sweep from 45deg to 315deg
        """
        # filling row from left to right
        
        quadratic_formation = list()
    
        break_row = 99
        start_row = 1
        for col in range(99, 51, -8):
            for row in range(start_row, break_row):
                quadratic_formation.append((col, row))
            break_row = break_row - 1
            start_row = start_row + 1
        return quadratic_formation

    def left_quadrant(self):
        """
            Goal: Precomputation 
            4. define a fourth arc and sweep from 135deg to 225deg
        """

        quadratic_formation = list()
        
        break_row = 99
        start_row = 1
        for col in range(0, 49, 8):
            for row in range(start_row, break_row):
                quadratic_formation.append((col, row))
            break_row = break_row - 1
            start_row = start_row + 1
        return quadratic_formation


# ---------------------------------------------------------------------------- #
#                               Main Player Class                              #
# ---------------------------------------------------------------------------- #

class Player:
    def __init__(self, rng: np.random.Generator, logger: logging.Logger, metabolism: float, goal_size: int,
                 precomp_dir: str) -> None:
        """Initialise the player with the basic amoeba information

            Args:
                rng (np.random.Generator): numpy random number generator, use this for same player behavior across run
                logger (logging.Logger): logger use this like logger.info("message")
                metabolism (float): the percentage of amoeba cells, that can move
                goal_size (int): the size the amoeba must reach
                precomp_dir (str): Directory path to store/load pre-computation
        """

        # precomp_path = os.path.join(precomp_dir, "{}.pkl".format(map_path))

        # # precompute check
        # if os.path.isfile(precomp_path):
        #     # Getting back the objects:
        #     with open(precomp_path, "rb") as f:
        #         self.obj0, self.obj1, self.obj2 = pickle.load(f)
        # else:
        #     # Compute objects to store
        #     self.obj0, self.obj1, self.obj2 = _

        #     # Dump the objects
        #     with open(precomp_path, 'wb') as f:
        #         pickle.dump([self.obj0, self.obj1, self.obj2], f)

        self.rng = rng
        self.logger = logger
        self.metabolism = metabolism
        self.goal_size = goal_size
        self.current_size = goal_size / 4

        self.formation = QuadraticFormationEnhanced()

    def move(self, last_percept, current_percept, info) -> (list, list, int):
        """Function which retrieves the current state of the amoeba map and returns an amoeba movement

            Args:
                last_percept (AmoebaState): contains state information after the previous move
                current_percept(AmoebaState): contains current state information
                info (int): byte (ranging from 0 to 256) to convey information from previous turn
            Returns:
                Tuple[List[Tuple[int, int]], List[Tuple[int, int]], int]: This function returns three variables:
                    1. A list of cells on the periphery that the amoeba retracts
                    2. A list of positions the retracted cells have moved to
                    3. A byte of information (values range from 0 to 255) that the amoeba can use
        """
        self.current_size = current_percept.current_size
        n_cells_can_move = int(self.metabolism * self.current_size)

        nAdjacentBacteria = 0
        for i, j in current_percept.bacteria:
            nAdjacentBacteria += 1
            current_percept.amoeba_map[i][j] = 1

        phase, count, isMoving, info = self.decode_info(info)
        # update byte of info
        BACTERIA_RATIO = 0.001 #TODO, maybe based on size of total amoeba and size of periphery??
        percent_bacteria = nAdjacentBacteria / len(current_percept.periphery)
        # print("percent_bacteria", percent_bacteria)
        count += 1 if percent_bacteria > BACTERIA_RATIO else -1
        count = max(0, count)
        count = min(7, count)
        #TODO: maybe once count at 7, just always use SpaceCurveFormation?
        # maybe just use 1 bit based on initial bacteria ratio?
        # all bacteria instantly run away
        # when is SFC better (0.3? 0.1?)?

        # if high density, use space filling curve
        # if count >= 6 or enough cells:
        #     self.formation == SpaceCurveFormation()

        self.formation.update(phase)
        goalFormation = self.formation.get_next_formation_points(current_percept)
        nCells = sum([sum(row) for row in current_percept.amoeba_map])
        firstCells = remove_duplicates(goalFormation)[:nCells]
        # plot_points_helper(firstCells)
        allRetractable = self.formation.get_all_retractable_points(firstCells, current_percept)

        allMovable = self.find_movable_cells(allRetractable, current_percept.periphery, current_percept.amoeba_map, current_percept.bacteria)
        toMove = self.formation.get_moveable_points(allMovable, firstCells, current_percept)

        retract, movable = self.formation.get_n_moves(allRetractable, toMove, current_percept, n_cells_can_move)
        
        phase = self.formation.get_phase(phase, current_percept, retract, movable)

        if len(retract) == 0 and len(movable) == 0:
            print("No moves")
        #     return self.move(last_percept, current_percept, self.encode_info(phase, count, 0, info))
        # else:
        #     isMoving = 1

        info = self.encode_info(phase, count, isMoving, info)

        return retract, movable, info

    def find_movable_cells(self, retract, periphery, amoeba_map, bacteria):
        '''
        Finds the cells that can be moved to given the retract
        :param retract: list of cells to retract
        :param periphery: list of cells on the periphery
        :param amoeba_map: map of the amoeba
        :param bacteria: list of bacteria
        :return: list of cells that can be moved
        '''
        movable = []
        new_periphery = list(set(periphery).difference(set(retract)))
        for i, j in new_periphery:
            nbr = self.find_movable_neighbor(i, j, amoeba_map, bacteria)
            for x, y in nbr:
                if (x, y) not in movable:
                    movable.append((x, y))

        movable += retract

        return movable

    def find_movable_neighbor(self, x, y, amoeba_map, bacteria):
        out = []
        if (x, y) not in bacteria:
            if amoeba_map[x][(y - 1) % 100] == 0:
                out.append((x, (y - 1) % 100))
            if amoeba_map[x][(y + 1) % 100] == 0:
                out.append((x, (y + 1) % 100))
            if amoeba_map[(x - 1) % 100][y] == 0:
                out.append(((x - 1) % 100, y))
            if amoeba_map[(x + 1) % 100][y] == 0:
                out.append(((x + 1) % 100, y))

        return out

    def encode_info(self, phase: int, count: int, isMoving: int, info: int) -> int:
        """Encode the information to be sent
            Args:
                phase (int): 2 bits for the current phase of the amoeba
                count (int): 3 bits for the current count of the running density
                isMoving (int): 1 bit for whether the amoeba is getting into position or not
                info (int): 2 bits other info, still TODO
            Returns:
                int: the encoded information as an int
        """
        assert phase < 4
        info = 0
        info_str = "{:02b}{:03b}{:01b}{:02b}".format(phase, count, isMoving, info)

        return int(info_str, 2)

    def decode_info(self, info: int) -> (int, int, int, int):
        """Decode the information received
            Args:
                info (int): the information received
            Returns:
                Tuple[int, int, int, int]: phase, count, isMoving, info, the decoded information as a tuple
        """
        info_str = "{0:b}".format(info).zfill(8)

        return int(info_str[0:2], 2), int(info_str[2:5], 2), int(info_str[5:6], 2), int(info_str[6:8], 2)



# UNIT TESTS
class TestAmoeba():
    def __init__(self):
        self.amoeba_map = [[0 for _ in range(100)] for _ in range(100)]
        self.size = 10
        startX = 50 - self.size // 2
        startY = 50 - self.size // 2
        for i in range(startX, startX + self.size):
            for j in range(startY, startY + self.size):
                self.amoeba_map[i][j] = 1
def show_formation_test():
    formation = RakeFormation()
    formation.update(1)
    points = formation.get_next_formation_points(TestAmoeba())
    x, y = zip(*points)
    plt.scatter(x, y)
    plt.xticks(range(min(x), max(y)+1))
    plt.savefig("formation.png")

if __name__ == '__main__':
    show_formation_test()