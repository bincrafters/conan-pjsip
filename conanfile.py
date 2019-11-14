from conans import ConanFile, AutoToolsBuildEnvironment, MSBuild, tools
from conans.errors import ConanInvalidConfiguration
from conans.model.version import Version
import os
import glob


class PJSIPConan(ConanFile):
    name = "pjsip"
    version = "2.9"
    description = "PJSIP is a free and open source multimedia communication library written in C language " \
                  "implementing standard based protocols such as SIP, SDP, RTP, STUN, TURN, and ICE"
    topics = ("conan", "pjsip", "sip", "voip", "multimedia", "sdp", "rtp", "stun", "turn", "ice")
    url = "https://github.com/bincrafters/conan-pjsip"
    homepage = "https://www.pjsip.org/"
    license = "GPL-2.0-or-later"
    exports = ["LICENSE.md"]
    exports_sources = ["patches/*.patch"]
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = "openssl/1.1.1d"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        if self.settings.compiler == "Visual Studio" and self.options.shared:
            # https://www.pjsip.org/pjlib/docs/html/group__pj__dll__target.htm
            raise ConanInvalidConfiguration("shared MSVC builds are not supported")

    def source(self):
        # Windows users MUST download the .zip because the files have CRLF line-ends,
        # while the .bz2 has LF line-ends and is for Unix and Mac OS X systems
        if self.settings.os == "Windows":
            source_url = "https://www.pjsip.org/release/{v}/pjproject-{v}.zip".format(v=self.version)
            sha256 = "4b467e57ca3eb4827af70d20e49741fda6066d7575abb5460768a36919add3c6"
        else:
            source_url = "https://www.pjsip.org/release/{v}/pjproject-{v}.tar.bz2".format(v=self.version)
            sha256 = "d185ef7855c8ec07191dde92f54b65a7a4b7a6f7bf8c46f7af35ceeb1da2a636"
        tools.get(source_url, sha256=sha256)
        os.rename("pjproject-" + self.version, self._source_subfolder)

    def build(self):
        if self.settings.compiler == "Visual Studio":
            self._build_msvc()
        else:
            self._build_configure()

    def _build_msvc(self):
        for filename in sorted(glob.glob("patches/*.patch")):
            self.output.info('applying patch "%s"' % filename)
            tools.patch(base_path=self._source_subfolder, patch_file=filename)
        # https://trac.pjsip.org/repos/wiki/Getting-Started/Windows
        with tools.chdir(self._source_subfolder):
            tools.save(os.path.join("pjlib", "include", "pj", "config_site.h"), "")
            version = Version(str(self.settings.compiler.version))
            sln_file = "pjproject-vs14.sln" if version >= "14.0" else "pjproject-vs8.sln"
            build_type = "Debug" if self.settings.build_type == "Debug" else "Release"
            if str(self.settings.compiler.runtime) in ["MT", "MTd"]:
                build_type += "-Static"
            else:
                build_type += "-Dynamic"
            msbuild = MSBuild(self)
            msbuild.build(project_file=sln_file, targets=["pjsua"], build_type=build_type,
                          platforms={"x86": "Win32", "x86_64": "x64"})

    def _build_configure(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "build.mak.in"),
                              "export TARGET_NAME := @target@",
                              "export TARGET_NAME := ")
        with tools.chdir(self._source_subfolder):
            args = ["--with-ssl=%s" % self.deps_cpp_info["openssl"].rootpath]
            if self.options.shared:
                args.extend(["--disable-static", "--enable-shared"])
            else:
                args.extend(["--disable-shared", "--enable-static"])
            # disable autodetect
            args.extend(["--disable-darwin-ssl",
                         "--enable-openssl",
                         "--disable-opencore-amr",
                         "--disable-silk",
                         "--disable-opus"])
            env_build = AutoToolsBuildEnvironment(self)
            env_build.configure(args=args)
            env_build.make()
            env_build.install()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        if self.settings.compiler == "Visual Studio":
            self.copy(pattern="*", src=os.path.join(self._source_subfolder, "pjlib", "include"),
                      dst="include", keep_path=True)
            self.copy(pattern="*", src=os.path.join(self._source_subfolder, "pjlib-util", "include"),
                      dst="include", keep_path=True)
            self.copy(pattern="*", src=os.path.join(self._source_subfolder, "pjnath", "include"),
                      dst="include", keep_path=True)
            self.copy(pattern="*", src=os.path.join(self._source_subfolder, "pjmedia", "include"),
                      dst="include", keep_path=True)
            self.copy(pattern="*", src=os.path.join(self._source_subfolder, "pjsip", "include"),
                      dst="include", keep_path=True)
            self.copy(pattern="*.lib", src=os.path.join(self._source_subfolder),
                      dst="lib", keep_path=False)

    def _format_lib(self, lib):
        return lib + "-"

    def package_info(self):
        libs = ["pjsua2",
                "pjsua",
                "pjsip-ua",
                "pjsip-simple",
                "pjsip",
                "pjmedia-codec",
                "pjmedia",
                "pjmedia-videodev",
                "pjmedia-audiodev",
                "pjnath",
                "pjlib-util",
                "srtp",
                "resample",
                "gsmcodec",
                "speex",
                "ilbccodec",
                "g7221codec",
                "yuv",
                "webrtc",
                "pj"]
        self.cpp_info.libs = [self._format_lib(lib) for lib in libs]
        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["m", "pthread"])
        elif self.settings.os == "Macos":
            self.cpp_info.frameworks = ["CoreAudio",
                                        "CoreServices",
                                        "AudioUnit",
                                        "AudioToolbox",
                                        "Foundation",
                                        "AppKit",
                                        "AVFoundation",
                                        "CoreGraphics",
                                        "QuartzCore",
                                        "CoreVideo",
                                        "CoreMedia",
                                        "VideoToolbox",
                                        "Security"]
        elif self.settings.os == "Windows":
            self.cpp_info.libs.extend(["wsock32", "ws2_32", "ole32", "dsound"])
