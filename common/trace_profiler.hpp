/**************************************************************************
 *
 * Copyright 2012 VMware, Inc.
 * All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 **************************************************************************/

#ifndef TRACE_PROFILER_H
#define TRACE_PROFILER_H

#include <string>
#include <vector>
#include <stdint.h>

namespace trace
{

struct Profile {
    struct CpuCall {
        unsigned no;

        int64_t cpuStart;
        int64_t cpuDuration;

        std::string name;
    };

    struct DrawCall {
        unsigned no;

        int64_t gpuStart;
        int64_t gpuDuration;

        int64_t cpuStart;
        int64_t cpuDuration;

        int64_t pixels;

        std::string name;
    };

    struct Frame {
        unsigned no;

        int64_t gpuStart;
        int64_t gpuDuration;

        int64_t cpuStart;
        int64_t cpuDuration;
    };

    struct Program {
        Program() : gpuTotal(0), cpuTotal(0), pixelTotal(0) {}

        uint64_t gpuTotal;
        uint64_t cpuTotal;
        uint64_t pixelTotal;
        std::vector<DrawCall> drawCalls;
    };

    std::vector<Frame> frames;
    std::vector<Program> programs;
    std::vector<CpuCall> cpuCalls;
};

class Profiler
{
public:
    Profiler();
    ~Profiler();

    void setup(bool cpuTimes_, bool gpuTimes_, bool pixelsDrawn_);

    void addCall(unsigned no,
                 const char* name,
                 unsigned program,
                 int64_t pixels,
                 int64_t gpuStart, int64_t gpuDuration,
                 int64_t cpuStart, int64_t cpuDuration);

    void addFrameEnd();

    bool hasBaseTimes();

    void setBaseCpuTime(int64_t cpuStart);
    void setBaseGpuTime(int64_t gpuStart);

    int64_t getBaseCpuTime();
    int64_t getBaseGpuTime();

    static void parseLine(const char* line, Profile* profile);

private:
    int64_t baseGpuTime;
    int64_t baseCpuTime;
    int64_t minCpuTime;

    bool cpuTimes;
    bool gpuTimes;
    bool pixelsDrawn;
};
}

#endif // TRACE_PROFILER_H
