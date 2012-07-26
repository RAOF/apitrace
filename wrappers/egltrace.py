##########################################################################
#
# Copyright 2011 LunarG, Inc.
# All Rights Reserved.
#
# Based on glxtrace.py, which has
#
#   Copyright 2011 Jose Fonseca
#   Copyright 2008-2010 VMware, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
##########################################################################/


"""EGL tracing generator."""


from gltrace import GlTracer
from specs.stdapi import API
from specs.glapi import glapi
from specs.eglapi import eglapi
from specs.glesapi import glesapi
import sys


class EglTracer(GlTracer):

    def __init__(self, isAndroid):
        self.isAndroid = isAndroid
        GlTracer.__init__(self)

    def manualTracking(self):
        return self.isAndroid

    def isFunctionPublic(self, function):
        # The symbols visible in libEGL.so can vary, so expose them all
        return True

    getProcAddressFunctionNames = [
        "eglGetProcAddress",
    ]

    def traceFunctionImplBody(self, function):
        GlTracer.traceFunctionImplBody(self, function)

        if function.name == 'eglCreateContext':
            print '    if (_result != EGL_NO_CONTEXT)'
            print '        gltrace::createContext((uintptr_t)_result);'

        if function.name == 'eglMakeCurrent':
            print '    if (_result) {'
            print '        // update the profile'
            print '        if (ctx != EGL_NO_CONTEXT) {'
            print '            EGLint api = EGL_OPENGL_ES_API, version = 1;'
            print '            gltrace::setContext((uintptr_t)ctx);'
            print '            gltrace::Context *tr = gltrace::getContext();'
            print '            _eglQueryContext(dpy, ctx, EGL_CONTEXT_CLIENT_TYPE, &api);'
            print '            _eglQueryContext(dpy, ctx, EGL_CONTEXT_CLIENT_VERSION, &version);'
            print '            if (api == EGL_OPENGL_API)'
            print '                tr->profile = gltrace::PROFILE_COMPAT;'
            print '            else if (version == 1)'
            print '                tr->profile = gltrace::PROFILE_ES1;'
            print '            else'
            print '                tr->profile = gltrace::PROFILE_ES2;'
            print '        } else {'
            print '            gltrace::clearContext();'
            print '        }'
            print '    }'

        if function.name == 'eglDestroyContext':
            print '    if (_result) {'
            print '        gltrace::releaseContext((uintptr_t)ctx);'
            print '    }'

if __name__ == '__main__':
    print '#include <stdlib.h>'
    print '#include <string.h>'
    print '#include <dlfcn.h>'
    print
    print '#include "trace_writer_local.hpp"'
    print
    print '// To validate our prototypes'
    print '#define GL_GLEXT_PROTOTYPES'
    print '#define EGL_EGLEXT_PROTOTYPES'
    print
    print '#include "glproc.hpp"'
    print '#include "glsize.hpp"'
    print
    
    api = API()
    api.addApi(eglapi)
    api.addApi(glapi)
    api.addApi(glesapi)
    is_android = "--android" in sys.argv
    tracer = EglTracer(is_android)
    tracer.traceApi(api)

    print r'''


/*
 * Android does not support LD_PRELOAD.
 */
#if !defined(ANDROID)


/*
 * Invoke the true dlopen() function.
 */
static void *_dlopen(const char *filename, int flag)
{
    typedef void * (*PFN_DLOPEN)(const char *, int);
    static PFN_DLOPEN dlopen_ptr = NULL;

    if (!dlopen_ptr) {
        dlopen_ptr = (PFN_DLOPEN)dlsym(RTLD_NEXT, "dlopen");
        if (!dlopen_ptr) {
            os::log("apitrace: error: dlsym(RTLD_NEXT, \"dlopen\") failed\n");
            return NULL;
        }
    }

    return dlopen_ptr(filename, flag);
}


/*
 * Several applications, such as Quake3, use dlopen("libGL.so.1"), but
 * LD_PRELOAD does not intercept symbols obtained via dlopen/dlsym, therefore
 * we need to intercept the dlopen() call here, and redirect to our wrapper
 * shared object.
 */
extern "C" PUBLIC
void * dlopen(const char *filename, int flag)
{
    bool intercept = false;

    if (filename) {
        intercept =
            strcmp(filename, "libEGL.so") == 0 ||
            strcmp(filename, "libEGL.so.1") == 0 ||
            strcmp(filename, "libGLESv1_CM.so") == 0 ||
            strcmp(filename, "libGLESv1_CM.so.1") == 0 ||
            strcmp(filename, "libGLESv2.so") == 0 ||
            strcmp(filename, "libGLESv2.so.2") == 0 ||
            strcmp(filename, "libGL.so") == 0 ||
            strcmp(filename, "libGL.so.1") == 0;

        if (intercept) {
            os::log("apitrace: redirecting dlopen(\"%s\", 0x%x)\n", filename, flag);

            /* The current dispatch implementation relies on core entry-points to be globally available, so force this.
             *
             * TODO: A better approach would be note down the entry points here and
             * use them latter. Another alternative would be to reopen the library
             * with RTLD_NOLOAD | RTLD_GLOBAL.
             */
            flag &= ~RTLD_LOCAL;
            flag |= RTLD_GLOBAL;
        }
    }

    void *handle = _dlopen(filename, flag);

    if (intercept) {
        // Get the file path for our shared object, and use it instead
        static int dummy = 0xdeedbeef;
        Dl_info info;
        if (dladdr(&dummy, &info)) {
            handle = _dlopen(info.dli_fname, flag);
        } else {
            os::log("apitrace: warning: dladdr() failed\n");
        }
    }

    return handle;
}


#endif /* !ANDROID */


#if defined(ANDROID)

/*
 * Undocumented Android extensions used by Dalvik which have bound information
 * passed to it, but is currently ignored, so probably unreliable.
 *
 * See:
 * https://github.com/android/platform_frameworks_base/blob/master/opengl/libs/GLES_CM/gl.cpp
 */

extern "C" PUBLIC
void APIENTRY glColorPointerBounds(GLint size, GLenum type, GLsizei stride, const GLvoid * pointer, GLsizei count) {
    (void)count;
    glColorPointer(size, type, stride, pointer);
}

extern "C" PUBLIC
void APIENTRY glNormalPointerBounds(GLenum type, GLsizei stride, const GLvoid * pointer, GLsizei count) {
    (void)count;
    glNormalPointer(type, stride, pointer);
}

extern "C" PUBLIC
void APIENTRY glTexCoordPointerBounds(GLint size, GLenum type, GLsizei stride, const GLvoid * pointer, GLsizei count) {
    (void)count;
    glTexCoordPointer(size, type, stride, pointer);
}

extern "C" PUBLIC
void APIENTRY glVertexPointerBounds(GLint size, GLenum type, GLsizei stride, const GLvoid * pointer, GLsizei count) {
    (void)count;
    glVertexPointer(size, type, stride, pointer);
}

extern "C" PUBLIC
void GL_APIENTRY glPointSizePointerOESBounds(GLenum type, GLsizei stride, const GLvoid *pointer, GLsizei count) {
    (void)count;
    glPointSizePointerOES(type, stride, pointer);
}

extern "C" PUBLIC
void APIENTRY glMatrixIndexPointerOESBounds(GLint size, GLenum type, GLsizei stride, const GLvoid *pointer, GLsizei count) {
    (void)count;
    glMatrixIndexPointerOES(size, type, stride, pointer);
}

extern "C" PUBLIC
void APIENTRY glWeightPointerOESBounds(GLint size, GLenum type, GLsizei stride, const GLvoid *pointer, GLsizei count) {
    (void)count;
    glWeightPointerOES(size, type, stride, pointer);
}

/*
 * There is also a glVertexAttribPointerBounds in
 * https://github.com/android/platform_frameworks_base/blob/master/opengl/tools/glgen/stubs/gles11/GLES20cHeader.cpp
 * but is it not exported.
 */

#endif /* ANDROID */


'''
