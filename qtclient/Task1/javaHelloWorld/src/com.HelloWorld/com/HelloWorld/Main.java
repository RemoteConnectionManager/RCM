package com.HelloWorld;

import javafx.application.Application;
import javafx.event.ActionEvent;
import javafx.event.EventHandler;
import javafx.scene.Scene;
import javafx.scene.text.*;
import javafx.scene.layout.StackPane;
import javafx.stage.Stage;

public class Main extends Application 
{

    @Override
    public void start(Stage primaryStage) 
    {
        Text t = new Text("Hello World");

	StackPane root = new StackPane();
        root.getChildren().add(t);

        Scene scene = new Scene(root, 300, 250);

        primaryStage.setTitle("Hello World!");
        primaryStage.setScene(scene);
        primaryStage.show();
    }

    public static void main(String[] args) 
    {
        launch(args);
    }
}
