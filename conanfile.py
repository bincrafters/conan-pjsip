from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os


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
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = "openssl/1.1.1d"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

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
        with tools.chdir(self._source_subfolder):
            args = ["--with-ssl=%s" % self.deps_cpp_info["openssl"].rootpath]
            if self.options.shared:
                args.extend(["--disable-static", "--enable-shared"])
            else:
                args.extend(["--disable-shared", "--enable-static"])
            env_build = AutoToolsBuildEnvironment(self)
            env_build.configure(args=args)
            env_build.make()
            env_build.install()

    def package(self):
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)

    def _format_lib(self, lib):
        suffix = {'Macos': '-x86_64-apple-darwin18.6.0',
                  'Linux': '-x86_64-unknown-linux-gnu'}.get(str(self.settings.os))
        return lib + suffix

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
