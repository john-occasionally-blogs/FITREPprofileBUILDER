# Product Requirements Document

Purpose: This file defines what we are building and for whom, focusing on the project's features, goals, and user experience.

> Use this file to outline what you're building and why. This guide helps you and your AI assistant understand the project goals, features, and user experience. Think of it as your project's blueprint that everyone can reference.

> You don’t need to be perfect here, just write in plain English. The AI will help refine.

---

## 1. The Big Picture (What are we making?)

> Start with the high-level overview. This section should give anyone reading this document a clear understanding of what you're building and who it's for.

* **Project Name:** FITREP Assistance Tool
* **One-Sentence Summary:** This tool is designed to take all of the effort out of maintaining your profile, and the guesswork out of what your relative value will be for the reports you are currently writing.
* **Who is this for?** This tool is for every Marine Corps officer who writes FITREPs.
* **What this app will NOT do:** This app will not replace communication between you and the Marines who work for you, or write the fitness reports (FITREPs) for you.

---

## 2. The Features (What can it do?)

> List the main features as "stories." This is a great way to explain what the app does from a user's perspective. User stories follow the format: "As a [type of user], I want to [take an action] so that I can [achieve a goal]."

* **Story 1:** As a Marine Officer, I want to be able to drag and drop all of my FITREPs into an app with a modern GUI, so that I can determine my current profile in preparation for writing new reports.
    * *Example: I drag and drop all of my FITREPs onto the app page, and be provided - by rank - what my average is per person, what my overall average is per rank, what my high and low marks are per rank, and what the relative value is for every Marine I have written on.*
* **Story 2:** As a Marine Officer, I want to upload my system averages so that I can quickly determine if the app and the Marine Corps definitive system have the same scores.
    * *Example: As a plant owner, I want to receive a notification on my phone so that I don't forget to water my plant.*
* **Story 3** As a Marine Officer, I am able to have the app add reports I am in the process of writing, so I am able to determine the impact to my averages if I write the reports as proposed, and so I know the relative value of the reports the Marines will receive.
* *Example: I want to add three new reports for Marines who have done an amazing job.  I want to determine on the spot the impact of those reports on the Marines I have previously written on.*
---

## 3. The Look and Feel (How should it vibe?)

> Describe the visual style and the main screens of your app. You don't need to be a designer - just describe what you want users to see and experience.

* **Overall Style:** Modern and light.  Should have a semi professional look because this is to process the reports that will determine whether or not Marines get promoted.
* **Main Colors:** Marine Corps color schemes.  Blue and red are prominent uniform colors and would work well.
* **Key Screens:** List the main screens and what important buttons or text should be on them. You don't need to be a designer!
    * **Screen 1: Select existing profile, update profile, or upload and Create Initial profile**
        * Screen with three buttons that works well when navigating from a computer, iPad, or iphone.
        * The three buttons allow you to: create a new profile, continue to an existing profile, or add additional reports to an existing profile.
    * **Screen 2: Looks like a web app version of a spreadsheet that displays details of your profile**
       * Screen 2 is where you go if you are returning to an existing profile, or where you will be sent after the app created the profile for you.
        * A box at the top of the page that lets you drop down from a list and click on the rank you would like to explore your profile for. (e.g., "GySgt").
        * When you have clicked a rank, it will display a table that includes all of the relevant values for every person you have written on for that rank (e.g., "Top of table says the rank name, then every row starts with a person's last name, and then follows with all of the details.").
        * A button to add an additional report or reports.  This is the real value of this app.  It allows the officer to take a known (their current profile) and illuminate what is unknown (the value of additional reports and the values they are CONSIDERING) before they are finalized and affect their overall profile.
    * **Screen 3: Screen to create a new profile**
       * Screen 3 is where you go if you need to create a new profile.
        * A box at the top of the page says drop your files here, and has a large landing space to drag PDF files over.
        * When you have dropped files, the screen should give you a series of status updates.  For example, received the 48 reports you have dropped.  Processing 1/48, 2/48, etc with an estimated total time remaining.
        * When the upload is complete, there should be a large button that you can click that will take you to your newly created profile.
     * **Screen 4: Screen to update an existing profile**
       * Screen 4 is where you go if you need to add reports to an existing profile.
        * The initial portion should look a lot like screen 2, and say something like, "Is this the profile you would like to update?".
        * There should be two buttons, either yes or no.  Clicking yes should take you to a screen very similiar to screen 3, and should have the same type of status messages.  If you click no, it should take you back to screen 1.
        * When the upload is complete, there should be a large button that gives you the option to either quit the app, or go to an updated screen 2.