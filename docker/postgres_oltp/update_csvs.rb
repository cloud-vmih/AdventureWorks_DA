#!/usr/bin/env ruby

# AdventureWorks for Postgres
#  by Lorin Thwaits

# How to use this file:

# Download "Adventure Works 2014 OLTP Script" from:
#   https://github.com/Microsoft/sql-server-samples/releases/download/adventureworks/AdventureWorks-oltp-install-script.zip

# Extract the .zip and copy all of the CSV files into the same folder containing
# this update_csvs.rb file and the install.sql file.

# Modify the CSVs to work with Postgres by running:
#   ruby update_csvs.rb

# Create the database and tables, import the data, and set up the views and keys with:
#   psql -c "CREATE DATABASE \"Adventureworks\";"
#   psql -d Adventureworks < install.sql

# (you may need to also add:  -U postgres  to the above two commands)

# All 68 tables are properly set up.
# All 20 views are established.
# 68 additional convenience views are added which:
#   * Provide a shorthand to refer to tables.
#   * Add an "id" column to a primary key or primary-ish key if it makes sense.

#   For example, with the convenience views you can simply do:
#       SELECT pe.p.firstname, hr.e.jobtitle
#       FROM pe.p
#         INNER JOIN hr.e ON pe.p.id = hr.e.id;
#   Instead of:
#       SELECT p.firstname, e.jobtitle
#       FROM person.person AS p
#         INNER JOIN humanresources.employee AS e ON p.businessentityid = e.businessentityid;

# Schemas for these views:
#   pe = person
#   hr = humanresources
#   pr = production
#   pu = purchasing
#   sa = sales
# Easily get a list of all of these in psql with:  \dv (pe|hr|pr|pu|sa).*

# Enjoy!


def decode_csv(bytes, csv_file)
  if bytes.start_with?("\xFF\xFE".b)
    bytes.force_encoding("UTF-16LE").encode("UTF-8")
  elsif bytes.start_with?("\xFE\xFF".b)
    bytes.force_encoding("UTF-16BE").encode("UTF-8")
  elsif bytes.byteslice(0, 200).to_s.count("\x00") > 20
    bytes.force_encoding("UTF-16LE").encode("UTF-8")
  else
    text = bytes.dup.force_encoding("UTF-8")
    return text if text.valid_encoding?

    fallback = File.basename(csv_file) == "Address.csv" ? "WINDOWS-1252" : "UTF-8"
    bytes.force_encoding(fallback).encode("UTF-8", invalid: :replace, undef: :replace, replace: "")
  end
end

def csv_quote_if_needed(part)
  return part unless part.include?("\t") || part.include?("\n") || part.include?('"') || part.start_with?("<")

  %("#{part}")
end

Dir.glob('./*.csv') do |csv_file|
  begin
  content = decode_csv(File.binread(csv_file), csv_file)
  content = content[1..-1] if content.start_with?("\uFEFF")
  content = content.delete("\u0000")

  is_pipes = content.include?("+|")
  is_needed = is_pipes || csv_file.end_with?('/Address.csv') || content.include?('"')
  next unless is_needed

  output = ""
  text = ""

  if is_pipes
    content.each_line do |line|
      line = line.gsub("|474946383961", "|\\\\x474946383961") # For GIF data
                 .gsub(/\"/, "\"\"")

      if line.strip.end_with?("&|")
        text << line.strip[0..-3]
        output << text.split("+|", -1).map { |part| csv_quote_if_needed(part) }.join("\t")
        output << "\n"
        text = ""
      else
        text << line.gsub(/\r?\n/, "\\n")
      end
    end
  else
    cleaned = content.gsub(/\&\|\n/, "\n").gsub(/\&\|\r\n/, "\n")
                     .gsub("\tE6100000010C", "\t\\\\xE6100000010C") # For geospatial data
                     .gsub(/\r\n/, "\n") # Make everything compatible with Windows -- change \r\n into just \n

    cleaned.each_line do |line|
      output << line.chomp.split("\t", -1).map { |part|
        csv_quote_if_needed(part.gsub(/\"/, "\"\""))
      }.join("\t")
      output << "\n"
    end
  end

  puts "Processing #{csv_file}"
  File.write(csv_file + ".xyz", output)
  File.delete(csv_file)
  File.rename(csv_file + ".xyz", csv_file)

  # Here's a list of files that get snagged here:
  #    Address.csv
  #    AWBuildVersion.csv
  #    CreditCard.csv
  #    Culture.csv
  #    Currency.csv
  #    Department.csv
  #    EmployeeDepartmentHistory.csv
  #    EmployeePayHistory.csv
  #    Product.csv
  #    ProductCostHistory.csv
  #    ProductModelIllustration.csv
  #    ProductReview.csv
  #    SalesOrderDetail.csv
  #    SalesTerritory.csv
  #    Shift.csv
  #    ShipMethod.csv
  #    ShoppingCartItem.csv
  #    SpecialOffer.csv
  #    Vendor.csv
  #    WorkOrder.csv
  rescue Encoding::InvalidByteSequenceError
    warn "Skipping #{csv_file}: invalid byte sequence"
  end
end
