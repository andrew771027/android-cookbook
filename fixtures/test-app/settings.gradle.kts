pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement{
    respositoriesMode.set(
        respositoriesMode.FAIL_ON_PROJECT_REPORS
    )

    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "AndroidCookbookFixture"

include(":app")