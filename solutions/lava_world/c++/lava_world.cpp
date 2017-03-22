#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <deque>


class Island {
    public:
        std::vector<Island*> connections;  // All islands that are connected to this one
        int Ax, Ay, Bx, By, number;
        Island(int topX, int topY, int botX, int botY, int num);
        void AddConnection(Island* conn);
        bool connectsWith(Island* otherIsland);
};

struct IslandHasher
{
  std::size_t operator()(const Island& l) const
  {
    using std::size_t;
    using std::hash;
    using std::string;

     // Compute individual hash values for first, second and third
            // http://stackoverflow.com/a/1646913/126995
    size_t res = 17;
    res = res * 31 + hash<int>()( l.Ax );
    res = res * 31 + hash<int>()( l.Ay );
    res = res * 31 + hash<int>()( l.Bx );
    res = res * 31 + hash<int>()( l.By );
    res = res * 31 + hash<int>()( l.number );
    
    return res;
  }
};

Island* CreateIsland(int number);
void BuildConnections(std::unordered_map<int, Island*> islands, Island* island);
std::vector<int> GetComponentislands(Island* startIsland, std::unordered_set<int> &visited);
bool** BuildMatrix(std::unordered_map<int, Island*> islands, int IslandCount);
bool** FillMatrix(bool** matrix, std::vector<int> component);

Island::Island(int topX, int topY, int botX, int botY, int num) {
    Ax = topX;
    Ay = topY;
    Bx = botX;
    By = botY;
    number = num;
}

void Island::AddConnection(Island* conn) {
    connections.push_back(conn);
}

bool Island::connectsWith(Island* otherIsland) {
    /* See if this Island connects with another Island */
    return Ax <= otherIsland->Bx && Bx >= otherIsland->Ax && Ay >= otherIsland->By && By <= otherIsland->Ay;
}


// bool testOverlaps();
int main() {
    // std::cout << testOverlaps() << std::endl;
    
    int IslandCount, queryCount;
    std::unordered_map<int, Island*> islands;  // key: Island Number value: Island Object
    std::cin >> IslandCount >> queryCount;
    
    for (int IslandNum = 1; IslandNum < IslandCount+1; IslandNum++) {
        Island* newIsland = CreateIsland(IslandNum);
        BuildConnections(islands, newIsland);
        islands[IslandNum] = newIsland;
    }

    // After we're done reading all the islands, turn their connections into a matrix
    bool** matrix = BuildMatrix(islands, IslandCount);

    islands.clear();  // Free the memory of the Island objects since they're not needed anymore'
    // Take the user input
    for (int i = 0; i < queryCount; i++) {
        int row, col;
        std::cin >> row >> col;
        std::cout << (matrix[row][col] ? "YES" : "NO") << std::endl;
    }
    return 0;
}

bool** BuildMatrix(std::unordered_map<int, Island*> islands, int IslandCount) {
    bool** matrix = new bool*[IslandCount+1];
    std::unordered_set<int> visited;

    for (int i = 0; i < IslandCount+1; i++) {
        bool* row = new bool[IslandCount+1];
        for (int j = 0; j < IslandCount+1; j++) {
            row[j] = false;
        }
        matrix[i] = row;
    }

    // Get the components of all islands and fill the matrix's connections'
    for (int i = 1; i < IslandCount+1; i++) {
        if (visited.find(i) != visited.end())
            continue;
        matrix[i][i] = true;
        
        std::unordered_map<int,Island*>::const_iterator got = islands.find(i);
        if ( got == islands.end() )
            continue;
        Island* Island = got->second;

        std::vector<int> componentIslands = GetComponentislands(Island, visited);
        matrix = FillMatrix(matrix, componentIslands);
    }

    return matrix;
}

bool** FillMatrix(bool** matrix, std::vector<int> component) {
    /* Adds the connections of a component to the matrix representation of a graph */
    for (int i = 0; i < component.size(); i++) {
        int IslandIdx = component[i];
        for (int j = i; j < component.size(); j++) {
            int IslandIdx2 = component[j];
            matrix[IslandIdx][IslandIdx2] = true;
            matrix[IslandIdx2][IslandIdx] = true;
        }
    }

    return matrix;
}

std::vector<int> GetComponentislands(Island* startIsland, std::unordered_set<int> &visited) {
    /* 
    Runs a BFS from the Island to get the components
    Returns a vector of the islands that are in a given component 
    */
    std::vector<int> componentIslands;
    std::deque<Island*> islandsToVisit; // the stack
    islandsToVisit.push_back(startIsland);
    visited.insert(startIsland->number);
    componentIslands.push_back(startIsland->number);
    while (!islandsToVisit.empty()) {
        Island* currentIsland = islandsToVisit.front();
        islandsToVisit.pop_front();
        for (int i = 0; i < currentIsland->connections.size(); i++) {
            Island* otherIsland = currentIsland->connections[i];
            if (visited.find(otherIsland->number) == visited.end()) {
                islandsToVisit.push_back(otherIsland);
                visited.insert(otherIsland->number);
                componentIslands.push_back(otherIsland->number);
            }
        }
    }

    return componentIslands;
}

void BuildConnections(std::unordered_map<int, Island*> islands, Island* island) {
    /* 
    Go through each Island saved and see if it connects to the we Island we're about to add.
    If they do, simply make the connection
    */
    std::vector<std::pair<const int, Island*>> keyValuePairs(islands.begin(), islands.end());
    for (int i = 0; i < keyValuePairs.size(); i++) {
        Island* otherIsland = keyValuePairs[i].second;

        if (otherIsland->connectsWith(island)) {
            island->AddConnection(otherIsland);
            otherIsland->AddConnection(island);
        }
    }
}

Island* CreateIsland(int number) {
    int topX, topY, botX, botY;
    std::cin >> topX >> topY >> botX >> botY;
    Island* island = new Island(topX, topY, botX, botY, number);

    return iZsland;
}

// bool testOverlaps() {
//     Island* Island1 = new Island(0, 50, 30, 40, 1);
//     Island* Island2 = new Island(30, 50, 60, 40, 1);
//     Island* Island3 = new Island(40, 40, 60, 1, 1);
//     Island* nonConnectingIsland = new Island(-20, -20, -20, -20, 1);
//     return (Island1->connectsWith(Island2) && Island2->connectsWith(Island3) && Island3->connectsWith(Island2) && Island2->connectsWith(Island1)
//      && !Island1->connectsWith(nonConnectingIsland) && !Island2->connectsWith(nonConnectingIsland) && !Island3->connectsWith(nonConnectingIsland));
// }
