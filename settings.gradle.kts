pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
    plugins {
        // Lets Gradle provision the JDK 17 toolchain that `:protocol` pins with
        // `jvmToolchain(17)`. Without it the build only works on a machine where
        // a JDK 17 happens to sit where Gradle's auto-detection looks.
        id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
    }
}

plugins {
    // Lets Gradle provision the JDK 17 toolchain that `:protocol` pins with
    // `jvmToolchain(17)`. Without it the build only works on a machine where
    // a JDK 17 happens to sit where Gradle's auto-detection looks.
    id("org.gradle.toolchains.foojay-resolver-convention")
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "AndroidUse"

include(":protocol")
include(":app")
include(":relay")
