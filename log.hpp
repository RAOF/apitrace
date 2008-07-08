/****************************************************************************
 *
 * Copyright 2008 Jose Fonseca
 *
 * This program is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 ****************************************************************************/

#ifndef _LOG_HPP_
#define _LOG_HPP_

#include <windows.h>
#include <tchar.h>
#include <stdio.h>


class File
{
public:
    File(const TCHAR *szName, const TCHAR *szExtension);
    ~File();

    void Open(const TCHAR *szName, const TCHAR *szExtension);
    void ReOpen(void);
    void Close(void);
    void Write(const char *szText);
    
private:
    HANDLE m_hFile;
    TCHAR szFileName[MAX_PATH];
};


class Log : public File
{
public:
    Log(const TCHAR *szName);
    ~Log();
    
    void NewLine(void);
    void Tag(const char *name);
    void BeginTag(const char *name);
    void BeginTag(const char *name, 
                  const char *attr1, const char *value1);
    void BeginTag(const char *name, 
                  const char *attr1, const char *value1,
                  const char *attr2, const char *value2);
    void EndTag(const char *name);
    void Text(const char *text);
    void TextF(const char *format, ...);
    void BeginCall(const char *function);
    void EndCall(void);
    void BeginParam(const char *name, const char *type);
    void EndParam(void);
    void BeginReturn(const char *type);
    void EndReturn(void);
    
protected:
    void Escape(const char *s);
};


extern Log * g_pLog;


#endif /* _LOG_HPP_ */
