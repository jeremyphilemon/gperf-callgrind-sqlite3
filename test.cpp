#include "gperftools/profiler.h"
#include <cmath>
#include <chrono>

double burn(unsigned long iterations = 10000000lu) {
  volatile double sum{0.0};
  double f;
  for (auto i = 0lu; i < iterations; ++i) {
    f = (double)(i+1) / iterations * 1.414;
    sum += std::sin(std::log(f));
  }
  return sum;
}

double burn_for(float ms_interval = 1.0) {
  volatile double burn_result{0.0};
  std::chrono::duration<float, std::milli> chrono_interval(ms_interval);
  auto start = std::chrono::system_clock::now();
  while (std::chrono::system_clock::now() - start < chrono_interval)
    burn_result += burn(20);

  return burn_result;
}

int main() {
  ProfilerStart("./dump.prof");
  burn_for(100000.0);
  ProfilerFlush();
  ProfilerStop();
  return 0;
}