from conans import ConanFile, CMake, tools
import os

class ProtobufConan(ConanFile):
    name = "protobufcpp"
    version = "3.6.1"
    author = "Ralph-Gordon Paul (gordon@rgpaul.com)"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "android_ndk": "ANY", "android_stl_type":["c++_static", "c++_shared"]}
    default_options = "shared=False", "android_ndk=None", "android_stl_type=c++_static"
    description = "Protocol Buffers - Google's data interchange format"
    url = "https://github.com/Manromen/conan-protobuf-cpp-scripts"
    exports_sources = "cmake-modules/*"
    generators = "cmake_paths"

    # download sources
    def source(self):
        url = "https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protobuf-cpp-%s.zip" % self.version
        tools.get(url)

        tools.replace_in_file("%s/protobuf-%s/cmake/CMakeLists.txt" % (self.source_folder, self.version),
            "project(protobuf C CXX)",
            """project(protobuf C CXX)
include(${CMAKE_BINARY_DIR}/conan_paths.cmake) """)

    # compile using cmake
    def build(self):

        cmake = CMake(self)
        cmake.verbose = True

        src_folder = "%s/protobuf-%s/cmake" % (self.source_folder, self.version)

        if self.settings.os == "Android":
            self.applyCmakeSettingsForAndroid(cmake)

        if self.settings.os == "iOS":
            self.applyCmakeSettingsForiOS(cmake)

        if self.settings.os == "Macos":
            self.applyCmakeSettingsFormacOS(cmake)

        if self.options.shared:
            cmake.definitions["BUILD_SHARED_LIBS"] = "ON"

        cmake.configure(source_folder=src_folder)
        cmake.build()
        cmake.install()

    def applyCmakeSettingsForAndroid(self, cmake):
        android_toolchain = os.environ["ANDROID_NDK_PATH"] + "/build/cmake/android.toolchain.cmake"
        cmake.definitions["CMAKE_SYSTEM_NAME"] = "Android"
        cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = android_toolchain
        cmake.definitions["ANDROID_NDK"] = os.environ["ANDROID_NDK_PATH"]
        cmake.definitions["ANDROID_ABI"] = tools.to_android_abi(self.settings.arch)
        cmake.definitions["ANDROID_STL"] = self.options.android_stl_type
        cmake.definitions["ANDROID_NATIVE_API_LEVEL"] = self.settings.os.api_level
        cmake.definitions["ANDROID_TOOLCHAIN"] = "clang"

    def applyCmakeSettingsForiOS(self, cmake):
        ios_toolchain = "cmake-modules/Toolchains/ios.toolchain.cmake"
        cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = ios_toolchain
        cmake.definitions["DEPLOYMENT_TARGET"] = "10.0"
        variants = []

        if self.settings.arch == "x86":
            cmake.definitions["IOS_PLATFORM"] = "SIMULATOR"
        elif self.settings.arch == "x86_64":
            cmake.definitions["IOS_PLATFORM"] = "SIMULATOR64"
        else:
            cmake.definitions["IOS_PLATFORM"] = "OS"

        # define all architectures for ios fat library
        if "arm" in self.settings.arch:
            variants = ["armv7", "armv7s", "armv8", "armv8.3"]

        # apply build config for all defined architectures
        if len(variants) > 0:
            archs = ""
            for i in range(0, len(variants)):
                if i == 0:
                    archs = tools.to_apple_arch(variants[i])
                else:
                    archs += ";" + tools.to_apple_arch(variants[i])
            cmake.definitions["ARCHS"] = archs
        else:
            cmake.definitions["ARCHS"] = tools.to_apple_arch(self.settings.arch)

    def applyCmakeSettingsFormacOS(self, cmake):
        cmake.definitions["CMAKE_OSX_ARCHITECTURES"] = tools.to_apple_arch(self.settings.arch)

    def requirements(self):
        self.requires("zlib/1.2.11@%s/%s" % (self.user, self.channel))
        
    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.includedirs = ['include']

    def package_id(self):
        if "arm" in self.settings.arch and self.settings.os == "iOS":
            self.info.settings.arch = "AnyARM"

    def config_options(self):
        # remove android specific option for all other platforms
        if self.settings.os != "Android":
            del self.options.android_ndk
            del self.options.android_stl_type
