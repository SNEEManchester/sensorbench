package avrora.sim.platform.sensors;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import avrora.Main;
import avrora.sim.mcu.Microcontroller;

/**
 * The <code>DirectSensorData</code> class implements a sensor data source that reads
 * the input values from a file, one after the other, and returns that information.
 *
 * @author lebiathan (George Valkanas)
 */
public class DirectSensorData implements SensorData {

    int currentIndex = 0;
	List values = new ArrayList();

    public DirectSensorData( Microcontroller m, String fn ) throws IOException {

    	/* Check if the file with the sensory values exists */
    	Main.checkFileExists( fn );

        try{
            String line = null;
            BufferedReader br = new BufferedReader( new FileReader( fn ) );

            while ( (line = br.readLine() ) != null ){
            	int iVal = Integer.parseInt( line );
            	values.add( new Integer( iVal ) );
            }

            br.close();

        }catch( Exception exc ){
        	exc.printStackTrace();
        }
    }


    public int reading() {

    	int value = ((Integer)values.get( currentIndex )).intValue();

    	value = value & 0x3ff;

    	/* Increase the size and modulo the input */
    	currentIndex++;
    	currentIndex = currentIndex % values.size();

    	/* Return the value that we have */
    	return value;
    }
}
